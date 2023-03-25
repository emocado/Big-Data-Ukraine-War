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
    time_stamp = datetime.utcnow().replace(second=0, microsecond=0)
    start_date = datetime.utcnow() - timedelta(minutes=15)
    bucket="tf-is459-ukraine-war-data"
    crawl_day = datetime.utcnow().strftime("%d-%m-%Y") # dd-mm-yyyy
    obj = s3.get_object(Bucket=bucket, Key='topics.txt')
    topics = obj['Body'].read().decode("utf-8").split("\n")

    try:
        for query in topics:
            posts = []
            posts_key=f"reddit_initial/topic={query}/dataload={crawl_day}/{time_stamp}.json"
            for post in reddit.subreddit("all").search(query=query , sort="new", time_filter="day", limit=100):
                if datetime.fromtimestamp(post.created_utc) < start_date:
                    break
                posts.append({
                    'id':str(post.id),
                    'date': str(datetime.fromtimestamp(post.created_utc)),
                    'title':str(post.title),
                    'content':str(post.selftext),
                    'username':str(post.author),
                    'subreddit':str(post.subreddit)
                })
                        
            posts_json = json.dumps(posts)
            response1 = s3.put_object(Body=posts_json, Bucket=bucket, Key=posts_key)
        return response1
    except Exception as e:
        print(e)
