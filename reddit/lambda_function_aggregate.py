import json
import boto3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import praw

load_dotenv()

client_id = os.environ.get("REDDIT_CLIENT_ID")
client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
password = os.environ.get("REDDIT_PASSWORD")
username = os.environ.get("REDDIT_USERNAME")
user_agent = os.environ.get("REDDIT_USER_AGENT")

print('Loading function')

s3 = boto3.client('s3')

reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    password=password,
    username=username,
    user_agent=user_agent
)

def lambda_handler(event, context):
    # Set the start and end dates for the search (in UTC timezone)

    # post_date = datetime.utcnow()
    time_stamp = datetime.utcnow().replace(second=0, microsecond=0)
    crawl_day = (datetime.utcnow() - timedelta(days=1)).strftime("%d-%m-%Y") # dd-mm-yyyy
    recrawl_day = time_stamp.strftime("%d-%m-%Y")
    bucket="tf-is459-ukraine-war-data"
    obj = s3.get_object(Bucket=bucket, Key='topics.txt')
    topics = obj['Body'].read().decode("utf-8").split("\n")
    
    for query in topics:
        updated_posts = []
        posts = []
        comments = []
        bucket_search_content = s3.list_objects_v2(Bucket=bucket, Prefix=f"reddit_initial/topic={query}/dataload={crawl_day}/").get('Contents', [])

        file_keys = [file['Key'] for file in bucket_search_content]
        for key in file_keys:
            post_file = s3.get_object(Bucket=bucket, Key=key)
            file_content = json.loads((post_file['Body'].read().decode("utf-8")))
            posts.extend(file_content)
    
        posts_key=f"project/reddit_posts/topic={query}/dataload={recrawl_day}/{time_stamp}_posts_aggregated.json"
        comments_key=f"project/reddit_comments/topic={query}/dataload={recrawl_day}/{time_stamp}_comments.json"

        for post in posts:
            try:
                updated_post = reddit.submission(id=post['id'])
                updated_posts.append({
                    'id':str(updated_post.id),
                    'date': str(datetime.fromtimestamp(updated_post.created_utc)),
                    'title':str(updated_post.title),
                    'content':str(updated_post.selftext),
                    'username':str(updated_post.author),
                    'subreddit':str(updated_post.subreddit),
                    'commentCount': int(updated_post.num_comments),
                    'score': int(updated_post.score),
                })
                if updated_post.num_comments > 0:
                    submission = reddit.submission(id=post['id'])
                    submission.comments.replace_more(limit=None)
                    for comment in submission.comments.list():
                        if str(comment.author) == "AutoModerator":
                            continue
                        if comment.author == None:
                            continue
                        comments.append({
                            'id': str(comment.id),
                            'date': str(datetime.fromtimestamp(comment.created_utc)),
                            'content': str(comment.body),
                            'username': str(comment.author.name),
                            'score': int(comment.score),
                            'post_id': str(updated_post.id),
                            'parent_id': str(comment.parent_id),
                        })
            except Exception as e:
                print(e)
            
        posts_json = json.dumps(updated_posts)
        comments_json = json.dumps(comments)
        response1 = s3.put_object(Body=posts_json, Bucket=bucket, Key=posts_key)
        response2 = s3.put_object(Body=comments_json, Bucket=bucket, Key=comments_key)        
    return response1, response2 
