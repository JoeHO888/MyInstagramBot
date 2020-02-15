import pandas as pd
import numpy as np
import pyodbc
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import re
import utils
import configparser
import os
from string import Template
import random
import time
import instabot

current_time = int(time.time())
print(f"-----Job is started at {current_time}-----")

config = configparser.ConfigParser()
config.read('config.ini')

server = config["AzureSQL"]["server"]
database = config["AzureSQL"]["database"]
username = config["AzureSQL"]["username"]
password = config["AzureSQL"]["password"]
driver = config["AzureSQL"]["driver"]

sentences_db_path = config["FilesPath"]["sentence"]
hashtags_db_path = config["FilesPath"]["hashtag"]
caption_template_path = config["FilesPath"]["caption_template"]
downloaded_img_folder_path = config["FilesPath"]["downloaded_img_folder"]

my_account_name = config["Credentials"]["Account"]
my_account_password = config["Credentials"]["Password"]

model_path = config["Model"]["Path"]
print("All configuration is imported")

cnxn = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)

print("Connection to SQL Server is established")

# Load SQL Table into Dataframe
# image_df = utils.load_image_table(cnxn)
df = utils.load_image_table(cnxn)
print("Photo Data is loaded")

# Change Column Name and Data Type
df = utils.format_data(df)

print("Photo Data is formatted")

# Extract insights from existing columns, e.g. weekday from unix epoch
df = utils.extract_data(df)

print("More insight is gained from Photo Data")

# Predict Score

# Apply delay function on Image Post Time and Image Original User Last Post Time

# best_photos_sorted
features = ["caption_length", "english_content_length", "english_content_ratio", "hashtag_count", "hashtag_total_length", "hashtag_avg_length", "hashtag_caption_ratio","mention_count", "year", "month", "weekday","week", "hour", "followers", "following", "follower_following_ratio"]
photos_ranking = utils.rank_photo(df, features, model_path, current_time)
# photos_ranking = [e for e in range(len(df))]
# random.shuffle(photos_ranking)

# Download Photo
downloaded_photo_path, row_num, image_id = utils.download_img(photos_ranking, df, downloaded_img_folder_path, current_time)
print(f"Selected Photo:{image_id} is downloaded")

# Generate Caption
original_caption = df.loc[row_num,"caption"]
print("Original caption is extracted")

# 1. Get Author UserName
author_id = df.loc[row_num,"user_id"]
print("Author ID is extracted")

author_name = utils.get_image_author(cnxn, author_id)
print("Author Name is retrieved")

# 2. Pick Hashtags (picking 30 hashtags and preserve 30% hashtags of original post by defaule)
english_hashtags = utils.get_english_hashtags(original_caption)
print("English Hashtags are extracted")

hashtags = utils.generate_hashtags(english_hashtags, path=hashtags_db_path)
print("All hashtags are generated")

# 3. Pick Sentences (picking 2 captions by default)
sentences = utils.pick_sentences(sentences_db_path)
print("Sentences in caption are generated")

# 4. Generate caption
caption = utils.generate_caption(author_name, sentences, hashtags, caption_template_path)
print("Caption is generated")

with open("Mydebug.txt","a") as f:
    f.write(caption + "\n" + utils.get_image_url(df.loc[row_num,"image_id"]))

# Login
bot = instabot.Bot()
bot.login(username=my_account_name, password=my_account_password)
print("Successfully log in")

# Pause a while
time.sleep(random.randint(5,15))

# Update Image DB: Change Image Availability
utils.update_image_availability(cnxn, image_id)
print(f"Id: Availability of Image ID: {row_num} is updated ")

# Post
bot.upload_photo(downloaded_photo_path, caption)
print("Successfully upload photo")

# Delete Image
os.remove(downloaded_photo_path+".REMOVE_ME")
print(f"Photo {downloaded_photo_path+'.REMOVE_ME'} is removed")

# Update User DB: Update Last Update Time
utils.update_user_last_post_time(cnxn, author_id, current_time)
print(f"Author ID: {author_id} 's Last Post Time is {current_time}")

cnxn.close()
print("SQL Server Connection is closed")
print(f"-----Job Completed in {str(int(time.time())-current_time)} s-----")
print("\n")
