import os
import random

following_src_path = "./following_db/following_src.txt"
current_following_path = "./following_db/current_following.txt"
new_following_number = 10

with open(following_src_path) as f:
    following_src = f.read().split("\n")

with open(current_following_path) as f:
    current_following = f.read().split("\n")


new_following_set = set()
current_following_set = set(current_following)

while len(new_following_set) <= new_following_number:
    following_id = random.choice(following_src)
    if not following_id in new_following_set or not following_id in current_following_set:
        new_following_set.add(following_id)

new_following = list(new_following_set)

current_following_shuffled = random.shuffle(current_following)

for i in range(len(new_following)):
    # follow new_following[i]
    # unfollow current_following_shuffled[i]    
    print(new_following[i])
    

