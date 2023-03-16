import sys
import json
import boto3
from deep_translator import GoogleTranslator

s3 = boto3.client('s3')
translator = GoogleTranslator(source='auto', target='en')
bucket = "is459-ukraine-war-data"
file_path = "project/russia war/"


def translate_tweet(filename):
    s3_response_object = s3.get_object(Bucket=bucket, Key=file_path+filename)
    json_content = json.loads(
        s3_response_object['Body'].read().decode('utf-8'))
    translated_content = []
    for obj in json_content:
        translated_content.append({
            "id": obj["id"],
            "date": obj["date"],
            "content": translator.translate(obj["content"]),
            "username": obj["username"],
            "followersCount": obj["followersCount"],
            "mentionedUsers": obj["mentionedUsers"],
            "retweetCount": obj["retweetCount"],
            "replyCount": obj["replyCount"],
            "inReplyToUser": obj["inReplyToUser"],
            "timeStamp": obj["timeStamp"]
        })
    return {
        'statusCode': 200,
        'result': json.dumps(translated_content)
    }


print(translate_tweet("2023-03-16 08:32:00.json"))
