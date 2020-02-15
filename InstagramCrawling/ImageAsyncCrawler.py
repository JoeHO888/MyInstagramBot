import json
import urllib

from .AsyncCrawler import AsyncCrawler

class ImageAsyncCrawler(AsyncCrawler):

    def __init__(self,root_urls, start, end, max_media_search=28,extract_extra_urls_needed=True, max_concurrency=20):
        super().__init__(root_urls, extract_extra_urls_needed, max_concurrency)
        self.start = start
        self.end = end
        self.max_media_search = max_media_search
        self.media_endpoint = 'https://www.instagram.com/graphql/query/?query_hash=42323d64886122307be10013ad2dcc44&variables=%s'
    
    def parse(self,html):
        raw_json = json.loads(html)
        try:
            media_full_data_array = raw_json["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
            return self.parser_helper(media_full_data_array)
        except:
            return []

    def parser_helper(self,media_full_data_array):
        img_selected_meta_data_array = []
        for i, media_meta_data in enumerate(media_full_data_array):
            img_post_date = int(media_meta_data["node"]["taken_at_timestamp"])
            media_is_video = media_meta_data["node"]["is_video"]

            # Select image after start date
            if self.start <= img_post_date <= self.end and not media_is_video:
                img_selected_meta_data = []
                # User ID
                img_selected_meta_data.append(int(media_meta_data["node"]["owner"]["id"]))
                # Image URL
                img_selected_meta_data.append(media_meta_data["node"]["id"])
                # Caption
                img_selected_meta_data.append(media_meta_data["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"])
                # Timestamp
                img_selected_meta_data.append(media_meta_data["node"]["taken_at_timestamp"])                            
                # Like Count
                img_selected_meta_data.append(media_meta_data["node"]["edge_media_preview_like"]["count"])
                # Comment Count
                img_selected_meta_data.append(media_meta_data["node"]["edge_media_to_comment"]["count"])                
            
                img_selected_meta_data_array.append(img_selected_meta_data)

            else:
                break
        return img_selected_meta_data_array
    
    def extract_url(self,html):
        new_urls = []
        try:
            raw_json = json.loads(html)
        
            has_next_page = raw_json["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]["has_next_page"]
            last_media_post_date = raw_json["data"]["user"]["edge_owner_to_timeline_media"]["edges"][-1]["node"]["taken_at_timestamp"]
            end_cursor = raw_json["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]["end_cursor"]
            owner_id = raw_json["data"]["user"]["edge_owner_to_timeline_media"]["edges"][-1]["node"]["owner"]["id"]

            if last_media_post_date > self.start and has_next_page:
                # next_page_url
                query_dict = {
                    'id': str(owner_id),
                    'first': str(self.max_media_search),
                    'after': str(end_cursor)
                }
                new_urls.append(self.extract_url_helper(query_dict))
        except:
            pass

        return new_urls
        
    def extract_url_helper(self, query_dict):
        return self.media_endpoint % urllib.parse.quote_plus(json.dumps(query_dict, separators=(',', ':')))