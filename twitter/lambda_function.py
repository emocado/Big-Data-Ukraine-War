import json
import urllib.parse
import boto3
import snscrape.modules.twitter as sntwitter
from datetime import datetime, timedelta

print('Loading function')

s3 = boto3.client('s3')


def lambda_handler(event, context):
    key=f"{datetime.utcnow().replace(second=0, microsecond=0)}.json"
    bucket="wklee-is459"
    query = "ukraine war"
    try:
        # Set the start and end dates for the search (in UTC timezone)
        start_date = datetime.utcnow()
        end_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        tweets = []
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(f"{query} since:{start_date.date()} until:{end_date.date()}").get_items()):
            if tweet.date.time() < (start_date - timedelta(minutes=15)).time():
                break
            tweets.append({
                'id': tweet.id,
                'date': tweet.date.strftime('%Y-%m-%d %H:%M:%S'),
                'content': tweet.rawContent,
                "username": tweet.user.username,
                "followersCount": tweet.user.followersCount,
                "mentionedUsers": ",".join([user.username for user in tweet.mentionedUsers]) if tweet.mentionedUsers else None,
                "retweetCount": tweet.retweetCount,
                "replyCount": tweet.replyCount,
                "inReplyToUser": tweet.inReplyToUser.username if tweet.inReplyToUser else None,
            })
        tweet_json = json.dumps(tweets)
        response = s3.put_object(Body=tweet_json, Bucket=bucket, Key=key)
        return response
    except Exception as e:
        print(e)
