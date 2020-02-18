# Instagram Influencer Bot under $6 on Azure
## An Instagram bot which sources photos from Instagram, selects the best photo among them with Machine Learning and post that photo everyday. On top of that, it follows and unfollows other Instagram accounts to boost followers.
##### Project inspired by [this medium post](https://medium.com/@chrisbuetti/how-i-eat-for-free-in-nyc-using-python-automation-artificial-intelligence-and-instagram-a5ed8a1e2a10)

### Factors to determine the best photos
1. Quality of photo (explained in below section)
2. Photo posted time
3. Last timestamp the original author post that photo

### Machine Learning
#### As mentioned above, we take quality of photo into account for selecting the best photo to post. During the selection, machine learning is adopted.
#### Before diving in the detail of machine learning, it is better to introduce the data scraped. Basically, the raw data looks like below.
| Photo ID | Caption      | Engagement Rate |
|----------|--------------|-----------------|
| ID 1     | I eat Apple  | 3.23%           |
| ID 2     | I eat Orange | 1.85%           |
###### Engagement Rate = (like + comment)/(followers of author)
##### Worth mentioning, I do not include the image although I am able to get the image and using deep learning, like [Convolutional neural network](https://en.wikipedia.org/wiki/Convolutional_neural_network) seems more straight forward to select the best photo. There are two reasons for that. First, using image for analysis possibly involve much more computation power, thus increases the cost. Second, I cannot find a good model for this task, as "good photo" is subjective.

#### After obtaining the raw data, some data engineering is performed to extract more insights, e.g. length of caption and number of hashtags. Then, I feed the processed data into [LightGBM](https://lightgbm.readthedocs.io/en/latest/) (a kind of machine learning model) to predict photo's engagement rate. Since the result is calculted purely by caption data and I assume engagement ratio is composed by caption and photo, so I subtract the real engagement rate by the predicted engagement rate to obtain the engagement rate that the photo can obtain if the photo is posted solely.

##### One more assumption is that the model is 100% correct to predict the engagement rate the caption brings to the post.

### Folder Structure
    .
    ├── Instagram                         # Bot to upload photos, follow and unfollow accounts
    │   ├── following_db                  # Contain files for bot to follow
    │   │   ├── following_src.txt         # Account ID row by row for bot to follow
    │   ├── follow_and_unfollow.py        # Python Script which lest bot to follow and unfollow instagram accounts
    │   ├── follow.sh                     # Bash Script which lets bot to follow and unfollow instagram accounts (for cron job)
    │   ├── main.sh                       # Bash Script which lets bot to upload photos (for cron job)    
    │   ├── upload.py                     # Python Script which lets bot to upload photos
    │   ├── utils.py                      # Helper function
    │   ├── config.ini                    # Config Files
    │   ├── caption_template.txt          # Template that bot uses to post phots    
    │   ├── hashtag.txt                   # Hashtags used in template    
    │   ├── sentence.txt                  # Sentences used in template
    │   ├── lgb_model.txt                 # Machine Learning Saved Model    
    ├── InstagramCrawling                 # Crawler to scrape photos  
    │   ├── __init__.py                   # Main function to run    
    │   ├── AsyncCrawler.py               # Async Crawler
    │   ├── ImageAsyncCrawler.py          # Image Crawler (Scrape images detail)
    │   ├── UserAsyncCrawler.py           # User Crawler (Scrape accounts detail)
    │   ├── utility.py                    # Helper function
