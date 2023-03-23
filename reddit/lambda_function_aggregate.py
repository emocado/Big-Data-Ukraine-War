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
    posts = []
    comments = []

    post_date = datetime.utcnow() - timedelta(days=3)
    time_stamp = datetime.utcnow().replace(second=0, microsecond=0)

    bucket="is459-ukraine-war-data"
    obj = s3.get_object(Bucket=bucket, Key='topics.txt')
    topics = obj['Body'].read().decode("utf-8").split("\n")
    for query in topics:
        bucket_search_content = s3.list_objects_v2(Bucket=bucket, Prefix=f"project/{query}/reddit/{str(post_date)[:10]}").get('Contents', [])
        file_keys = [file['Key'] for file in bucket_search_content]

    for key in file_keys:
        post_file = s3.get_object(Bucket=bucket, Key=key)
        file_content = json.load((post_file['Body'].read().decode("utf-8")))
        posts.extend(file_content)

    try:
        posts_key=f"project/{query}/reddit/{time_stamp}_posts_aggregated.json"
        comments_key=f"project/{query}/reddit/{time_stamp}_comments.json"
        for post in posts:
            updated_post = reddit.submission(id=post['id'])
            post['commentCount'] = int(updated_post.num_comments)
            post['score'] = int(updated_post.score)
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

        posts_json = json.dumps(posts)
        comments_json = json.dumps(comments)
        response1 = s3.put_object(Body=posts_json, Bucket=bucket, Key=posts_key)
        response2 = s3.put_object(Body=comments_json, Bucket=bucket, Key=comments_key)
        return response1, response2
    except Exception as e:
        print(e)
