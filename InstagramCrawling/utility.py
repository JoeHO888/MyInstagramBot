import os
import pyodbc
import urllib
import json
import logging

def establish_sql_connection():
    driver = os.environ["SQLDriver"]
    server = os.environ["SQLServer"]
    database = os.environ["SQLDatabase"]
    user = os.environ["SQLUser"]
    pwd = os.environ["SQLPassword"]
    config = os.environ["SQLOtherSettings"]

    cmd = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={user};PWD={pwd};{config}"
    try:
        cnxn = pyodbc.connect(cmd)
        return cnxn
    except:
        logging.info('Fail to connect to SQL DB')
        return None

def create_image_query_url(user_id,count, media_endpoint='https://www.instagram.com/graphql/query/?query_hash=42323d64886122307be10013ad2dcc44&variables=%s',end_cursor=""):
    query_dict = {
        'id': str(user_id),
        'first': str(count),
        'after': str(end_cursor)
    }
    
    return media_endpoint % urllib.parse.quote_plus(json.dumps(query_dict, separators=(',', ':')))    


def create_users_url(user_name, base_url="https://www.instagram.com/%s/"):
    return base_url % user_name

def img_data_to_string(img_data):
    record_string_array = []
    # record = UserId, Image URL, Caption, Timestamp, Like Count, Comment Count, Followers,  Following
    for record in img_data:        
        ele_array = []
        for i, ele in enumerate(record):
            if i == 2:
                ele = "N'" + ele.replace("'","''") + "'"
            if i == 1:
                ele = "'" + ele + "'"
            ele_array.append(str(ele))
        ele_array.append(str(1))   
        record_string_body = ", ".join(ele_array)
        record_string_array.append(f"({record_string_body})")
    full_record_string = ",\n".join(record_string_array)
    return full_record_string