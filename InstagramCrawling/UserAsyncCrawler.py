import re
import json

from .AsyncCrawler import AsyncCrawler

class UserAsyncCrawler(AsyncCrawler):

    def __init__(self,root_urls, extract_extra_urls_needed=False, max_concurrency=20):
        super().__init__(root_urls, extract_extra_urls_needed, max_concurrency)

    def parse(self, html):
        try:
            raw_data_array = re.findall(r'_sharedData = .*?;</script>', html)
            if len(raw_data_array) > 0:
                raw_json = json.loads(raw_data_array[0][len("_sharedData ="):-len(";</script>")])
            
                user_meta_data_json = raw_json['entry_data']['ProfilePage'][0]['graphql']['user']
            
                return self.parser_helper(user_meta_data_json)
        except:
            return []
    
    def parser_helper(self,user_meta_data_json):
        user_meta_data_record = []
        user_meta_data_record.append(int(user_meta_data_json["id"]))
        user_meta_data_record.append(user_meta_data_json["edge_followed_by"]["count"])
        user_meta_data_record.append(user_meta_data_json["edge_follow"]["count"])     
        return user_meta_data_record