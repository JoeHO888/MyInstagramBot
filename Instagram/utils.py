import pandas as pd
import numpy as np
import pyodbc
import lightgbm as lgb
from sklearn.model_selection import train_test_split
import re
import random
from string import Template
import requests
import time

def load_image_table(cnxn, follower_threshold=2000):
    image_sql_command = f"SELECT UserId, ImageId, Caption, PostTime, LikeCount, CommentCount, FollowerCount, FollowingCount, ImageAvailability FROM InstagramImage WHERE FollowerCount>={follower_threshold}"
    image_df = pd.read_sql(image_sql_command,cnxn)
    user_sql_command = "SELECT UserId, LastPostUnixTime FROM InstagramUser"
    user_df = pd.read_sql(user_sql_command,cnxn)
    return pd.merge(image_df, user_df, on='UserId', how='inner')

def update_image_availability(cnxn, image_id):
    sql_command = f"UPDATE InstagramImage SET ImageAvailability = 0 WHERE ImageId = {image_id};"
    cursor = cnxn.cursor()
    cursor.execute(sql_command)
    cursor.close()
    cnxn.commit()

def update_user_last_post_time(cnxn, author_id, update_time):
    sql_command = f"UPDATE InstagramUser SET LastPostUnixTime = {str(int(update_time))} WHERE UserId = {author_id};"
    cursor = cnxn.cursor()
    cursor.execute(sql_command)
    cursor.close()
    cnxn.commit()

def load_image_table_test(cnxn):
    sql_command = "SELECT UserId, ImageId, Caption, PostTime, LikeCount, CommentCount, FollowerCount, FollowingCount, ImageAvailability FROM InstagramImage"
    df = pd.read_sql(sql_command,cnxn)
    return df

def rank_photo(df, features, path, current_time, target_cols=["engagement_rate"],created_time=["created_time"],image_availability=["image_availability"],last_post_time=["last_post_unix_time"]):
    bst = lgb.Booster(model_file=path)
    y = (df.loc[:,target_cols].values.flatten() - bst.predict(df.loc[:,features].values) )* generate_photo_ranking_factor(df,current_time,created_time,image_availability, last_post_time)
    return np.argsort(-y)

def generate_photo_ranking_factor(df,current_time,created_time,image_availability, last_post_time, criteria=604800, factor=1000000000, power=0.5):
    threshold = current_time - criteria
    # Lower Importance of recent phots
    created_time_arr = df.loc[:,created_time].values
    a = (np.where(created_time_arr < threshold, created_time_arr, 2*threshold-created_time_arr)/factor)**power
    # Lower Importance of photos which come from recent users
    b = (df.loc[:, last_post_time].values/factor)**power
    c = df.loc[:,image_availability].values
    return (a*b*c).flatten()

def download_img(photos_ranking,df, folder, filename,image_id_col ="image_id"):
    for i in photos_ranking:
        image_url = get_image_url(df.loc[i,"image_id"])
        req = requests.get(image_url)
        if req.status_code == 200:
            extension = "jpg"
            path = f"{folder}/{filename}.{extension}"
            with open(path, 'wb') as f:    
                f.write(req.content)
            break
    return path,i,int(df.loc[i, image_id_col])


def get_image_author(cnxn,owner_id):
    sql = f"SELECT UserName FROM InstagramUser WHERE UserId={str(owner_id)}"
    df = pd.read_sql(sql,cnxn)
    return df.loc[0,"UserName"]

def pick_sentences(path, sentence_num=2):
    with open(path, "r") as f:  
        content = f.read()
    sentences = content.split("\n")
    return random.sample(sentences,sentence_num)

def get_english_hashtags(caption):
    english_hashtags = re.findall("#([a-z|A-Z|0-9|_]+)", caption)
    return english_hashtags

def generate_hashtags(english_hashtags, path, ratio = 0.3,hashtags_count = 30):
    with open(path, "r") as f:
        content = f.read()
    hashtags_db = content.split("\n")

    hashtags_set = set(["#"+e for e in random.sample(english_hashtags, int(len(english_hashtags)*ratio))])

    while len(hashtags_set) < hashtags_count:
        hashtags_set.add(random.choice(hashtags_db))

    hashtags = list(hashtags_set)
    random.shuffle(hashtags)
    return hashtags

def generate_caption(author_name, sentences, hashtags, caption_template_path):
    with open(caption_template_path, "r") as f:  
        template = Template(f.read())
    sub_dict={'author_name':author_name, 'hashtags':" ".join(hashtags), 'sentences':"\n".join(sentences)}
    caption = template.substitute(sub_dict)
    return caption

def format_data(df):

    # Change Columns Data Type
    for col in  ["PostTime", "LikeCount", "CommentCount", "FollowerCount", "FollowingCount"]:
        df[col] = df[col].astype("uint32")

    # Rename Columns
    df.rename(columns={"UserId": "user_id", "ImageId": "image_id",
                       "Caption":"caption", "PostTime": "created_time", 
                       "LikeCount": "like_count", "CommentCount": "comment_count", 
                       "FollowerCount": "followers", "FollowingCount": "following",
                       "ImageAvailability":"image_availability", "LastPostUnixTime": "last_post_unix_time"
                       },inplace=True)

    return df

def extract_data(df):
    # caption
    df["caption_length"] = (df["caption"].apply(lambda x: len(x))).astype(np.uint16)

    # english content
    df["english_content_length"] = (df["caption"].apply(lambda x: len([c for c in x if c.isalnum()]))).astype(np.uint16)
    df["english_content_ratio"] = (df["english_content_length"]/df['caption_length']).fillna(0)

    # hashtag
    df['hashtag_count'] = (df['caption'].apply(lambda x: len(re.findall("#([\S]+)", x)))).astype(np.uint8)
    df['hashtag_total_length'] = (df['caption'].apply(lambda x: len("".join(re.findall("#([\S]+)", x))))).astype(np.uint16)
    df['hashtag_avg_length'] = (df['hashtag_total_length'] / df['hashtag_count']).fillna(0)
    df['hashtag_caption_ratio'] = (df['hashtag_total_length'] / df['caption_length']).fillna(0)

    # mention
    df['mention_count'] = (df['caption'].apply(lambda x: len(re.findall("@([\S]+)", x)))).astype(np.uint8)

    # weekday, time, year, month, day, week
    df["timestamp"] = pd.to_datetime(df['created_time'],unit='s')
    df["year"] = df['timestamp'].dt.year.astype(np.uint8)
    df["month"] = df['timestamp'].dt.month.astype(np.uint8)
    df["weekday"] = df['timestamp'].dt.weekday.astype(np.uint8)
    df["week"] = df['timestamp'].dt.week.astype(np.uint8)
    df["hour"] = df['timestamp'].dt.hour.astype(np.uint8)

    # engagement
    df["engagement"] = df["like_count"]+ df["comment_count"]
    df["engagement_rate"] = (df["engagement"] / df["followers"]).fillna(0)

    # follower_following_ratio
    df["follower_following_ratio"] = (df["followers"] / df["following"]).fillna(0)

    return df

def get_image_url(photo_id):
    if photo_id.find("_"):
        media_id = photo_id.split("_")[0]

    alphabet = {
        "-": 62,
        "1": 53,
        "0": 52,
        "3": 55,
        "2": 54,
        "5": 57,
        "4": 56,
        "7": 59,
        "6": 58,
        "9": 61,
        "8": 60,
        "A": 0,
        "C": 2,
        "B": 1,
        "E": 4,
        "D": 3,
        "G": 6,
        "F": 5,
        "I": 8,
        "H": 7,
        "K": 10,
        "J": 9,
        "M": 12,
        "L": 11,
        "O": 14,
        "N": 13,
        "Q": 16,
        "P": 15,
        "S": 18,
        "R": 17,
        "U": 20,
        "T": 19,
        "W": 22,
        "V": 21,
        "Y": 24,
        "X": 23,
        "Z": 25,
        "_": 63,
        "a": 26,
        "c": 28,
        "b": 27,
        "e": 30,
        "d": 29,
        "g": 32,
        "f": 31,
        "i": 34,
        "h": 33,
        "k": 36,
        "j": 35,
        "m": 38,
        "l": 37,
        "o": 40,
        "n": 39,
        "q": 42,
        "p": 41,
        "s": 44,
        "r": 43,
        "u": 46,
        "t": 45,
        "w": 48,
        "v": 47,
        "y": 50,
        "x": 49,
        "z": 51,
    }
    result = ""
    while photo_id:
        photo_id, char = int(photo_id) // 64, int(photo_id) % 64
        result += list(alphabet.keys())[list(alphabet.values()).index(char)]
    return "https://instagram.com/p/" + result[::-1] + "/" + "media/?size=l"
