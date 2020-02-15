import configparser
import instabot
import random
import time

current_time = int(time.time())
print(f"-----Job is started at {current_time}-----")

config = configparser.ConfigParser()
config.read('config.ini')

following_db_path = config["Others"]["FollowingDBPath"]
new_following_num = config["Others"]["NewFollowingNum"]
following_removal_num = config["Others"]["FollowingRemovalNum"]

sleep_time_config_start = config["Others"]["SleepTimeConfigStart"]
sleep_time_config_end = config["Others"]["SleepTimeConfigEnd"]

my_account_name = config["Credentials"]["Account"]
my_account_password = config["Credentials"]["Password"]
my_account_id= config["Credentials"]["id"]

print("All configuration is imported")

with open(following_db_path ,"r") as f:
    following_db_src = f.read().split("\n")

bot = instabot.Bot()
bot.login(username=my_account_name, password=my_account_password,use_cookie=False)

selected_unfollowing  = random.sample(bot.get_user_following(int(my_account_id)),int(following_removal_num))

for i in range(len(selected_unfollowing)):
    time.sleep(random.randint(int(sleep_time_config_start),int(sleep_time_config_end)))
    bot.unfollow(selected_unfollowing[i])

print("Successfully unfollow accounts")

selected_following = random.sample(following_db_src,int(new_following_num))
for i in range(len(selected_following)):
    time.sleep(random.randint(int(sleep_time_config_start),int(sleep_time_config_end)))
    bot.follow(selected_following[i],False)

print("Successfully follow accounts")

print(f"-----Job is completed in {str(int(time.time() - current_time))}-----")
