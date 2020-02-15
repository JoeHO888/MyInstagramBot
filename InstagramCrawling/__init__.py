from .ImageAsyncCrawler import ImageAsyncCrawler
from .UserAsyncCrawler import UserAsyncCrawler
from . import utility
import os
import logging
import time
import math
from twilio.rest import Client

import azure.functions as func


def main(mytimer: func.TimerRequest) -> None:
    logging.info('Starting Main Function...')

    # Crawling Interval = number of seconds in a week
    crawling_interval = int(os.environ["CrawlingInterval"])
    period = int(os.environ["Period"])
    end = (int(time.time())//crawling_interval)*crawling_interval
    start = end - period * 24 * 60 * 60

    # 21 = 7 (days in a week) * 3 (max media per day)
    count = int(os.environ["Period"])*int(os.environ["MaxMediaCount"])

    cycle_num = int((end % (24*60*60)) / crawling_interval)
    user_per_cycle = int(math.floor(1175/(int(24*60*60/crawling_interval)-1)))

    user_pk_start = cycle_num * user_per_cycle
    user_pk_end = (cycle_num + 1) * user_per_cycle

    logging.info(user_pk_start)
    logging.info(user_pk_end)

    image_urls = []
    users_urls = []

    user_meta_data_mapping = {}
    image_data = []

    user_failure = 0
    img_failure = 0

    logging.info('Connecting To SQL Server')
    cnxn = utility.establish_sql_connection()

    account_sid = os.environ["TwilioAccount"]
    auth_token = os.environ["TwilioPassword"]
    my_phone_num = os.environ["PhoneNumber"]
    client = Client(account_sid, auth_token)

    # Connect To SQL Server
    if not cnxn:
		# 14155238886 is Twillo's sandbox Phone Number
        message = client.messages.create(body='Your message code is\nFail To Connect To SQL Server', from_='whatsapp:+14155238886', to='whatsapp:%s'%my_phone_num)
    with cnxn:
        # Fetch Users ID and Name
        cursor = cnxn.cursor()
        cursor.execute(f"SELECT * FROM [dbo].[InstagramUser] WHERE Id>={user_pk_start} AND Id<{user_pk_end}")
        row = cursor.fetchall()
        
        # Create URLs for crawling
        for _, user_id, user_name, _ in row:
            image_urls.append(utility.create_image_query_url(user_id, count))
            users_urls.append(utility.create_users_url(user_name))
        
        # Crawl Images (Async)
        image_crawler = ImageAsyncCrawler(image_urls,start=start,end=end)
        image_crawler.run()
        
        # Crawl User (Async)
        user_crawler = UserAsyncCrawler(users_urls)
        user_crawler.run()

        for user_meta_data in user_crawler.data:
            # user_meta_data: UserId, Followers, Following
            if user_meta_data and user_meta_data[0]:
                user_meta_data_mapping[user_meta_data[0]] = [user_meta_data[1], user_meta_data[2]]
            else:
                user_failure += 1


        # Flat image_crawler data
        for batch in image_crawler.data:
            for img_record in batch:
                # img_record: UserId, Image Id, Caption, Timestamp, Like Count, Comment Count
                if img_record and img_record[0] in user_meta_data_mapping:
                    # Add Owner's Followers and Following Number
                    img_record.append(user_meta_data_mapping[img_record[0]][0])
                    img_record.append(user_meta_data_mapping[img_record[0]][1])
                    image_data.append(img_record)
                else:
                    img_failure += 1
        

        insert_command_body = utility.img_data_to_string(image_data)
        insert_command = f"INSERT INTO [dbo].[InstagramImage] ( [UserId], [ImageId], [Caption], [PostTime], [LikeCount], [CommentCount], [FollowerCount], [FollowingCount], [ImageAvailability]) VALUES {insert_command_body};"
        logging.info(insert_command)
        cursor.execute(insert_command)
        cnxn.commit()
        
        # logging.info(insert_command)

        logging.info(str(len(image_data)))
        logging.info(str(user_failure))
        logging.info(str(img_failure))

    if user_failure > 0 and img_failure > 0:
        body = f"Your message code is\nUser Failure: {str(user_failure)}\nImage Failure: {str(img_failure)}"
		# 14155238886 is Twillo's sandbox Phone Number
        message = client.messages.create(body=body, from_='whatsapp:+14155238886', to='whatsapp:%s'%my_phone_num)
