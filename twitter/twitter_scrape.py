import json
import boto3
import snscrape.modules.twitter as sntwitter
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import os
import requests


def lambda_handler(event, context):
    
    # Get the Twitter API credentials from AWS Secrets Manager
    secret_name = os.environ['TWITTER_SECRETS_NAME']
    region_name = os.environ['AWS_REGION']
    client = boto3.client('secretsmanager', region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secrets = json.loads(response['SecretString'])

    # Authenticate with Twitter API using the credentials
    headers = {
        'Authorization': f"Bearer {secrets['access_token']}"
    }

    # Set the search query
    query = os.environ['QUERY']
    
    # Set the start and end dates for the search (in UTC timezone)
    end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=7)

    # Define the S3 bucket and key where the data will be stored
    bucket_name = os.environ['BUCKET_NAME']
    key = os.environ['BUCKET_KEY']

    # Create an S3 client and check if the bucket exists
    s3 = boto3.client('s3')
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError:
        # The bucket does not exist, so create it
        s3.create_bucket(Bucket=bucket_name)

    # Collect the data from Twitter using snscrape and store it in a list
    tweets = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(f"{query} since:{start_date.date()} until:{end_date.date()}").get_items()):
        tweets.append({
            'id': tweet.id,
            'date': tweet.date.strftime('%Y-%m-%d %H:%M:%S'),
            'content': tweet.content
        })

    # Write the data to an S3 object
    s3.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(tweets))
    
    return {
        'statusCode': 200,
        'body': 'Data collected and stored in S3'
    }
