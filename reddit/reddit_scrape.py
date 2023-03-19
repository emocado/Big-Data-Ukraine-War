import json
from datetime import datetime, timedelta
import praw

query = 'ukraine war'

reddit = praw.Reddit(
    client_id="m9BYSa5sn4PPK6cz91s4ZA",
    client_secret="IexB6l0s3CdUYjWj4PCl-GSCbtdI_A",
    password="P@ssword123",
    username="apple-tree3",
    user_agent="IS459-BigData/1.0.0"
)

posts = []
comments = []
start_date = datetime.utcnow()
time_stamp = start_date.replace(second=0, microsecond=0)

for post in reddit.subreddit("all").search(query=query , sort="new", time_filter="all", limit=100):
    try:
        if post.title != "[removed]" and post.title != "[deleted]" and post.title != "[deleted by user]":
            # if datetime.fromtimestamp(post.created_utc) < (start_date - timedelta(minutes=15)):
            #     continue
            if "https" in post.selftext or post.selftext == "":
                continue
            posts.append({
                'id':str(post.id),
                'date': str(datetime.fromtimestamp(post.created_utc)),
                'title':str(post.title),
                'content':str(post.selftext),
                'username':str(post.author),
                'commentCount':int(post.num_comments),
                'score':int(post.score),
                'subreddit':str(post.subreddit)
            })
            if post.num_comments > 0:
                submission = reddit.submission(id=post.id)
                for top_level_comment in submission.comments:
                    if str(top_level_comment.author) == "AutoModerator":
                        continue
                    comments.append({
                        'id': str(top_level_comment.id),
                        'date': str(datetime.fromtimestamp(top_level_comment.created_utc)),
                        'content': str(top_level_comment.body),
                        'username': str(top_level_comment.author.name),
                        'score': int(top_level_comment.score),
                        'post_id': str(post.id)
                    })
    except:
        print("Error: " + str(post.id))
        continue
            
with open (f"reddit/reddit_posts_dump.json", "w") as f:
    json.dump(posts, f)
with open (f"reddit/reddit_comments_dump.json", "w") as f:
    json.dump(comments, f)

print(len(posts))
print(len(comments))