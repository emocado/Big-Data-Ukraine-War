import json
import boto3
from deep_translator import GoogleTranslator
from typing import Dict, List


def fetch_data_catalog() -> List[Dict[str, str]]:
    glue = boto3.client('glue')
    catalog_table = glue.get_table(
        DatabaseName="twitter-crawler-database", Name='project')
    data_columns = catalog_table["Table"]["StorageDescriptor"]["Columns"]
    return data_columns


def translate_tweet(filename: str):
    s3 = boto3.client('s3')
    bucket = "is459-ukraine-war-data"
    file_path = "project/russia war/twitter/"
    translator = GoogleTranslator(source='auto', target='english')

    data_columns = fetch_data_catalog()
    content_obj = {}
    for index, column in enumerate(data_columns):
        column_key = column['Name']
        content_obj[column_key] = None

    translated_content = []
    s3_response_obj = s3.get_object(Bucket=bucket, Key=file_path+filename)
    json_content = json.loads(s3_response_obj['Body'].read())
    for obj in json_content:
        for key, value in obj.items():
            if key == "content":
                content_obj[key] = translator.translate(value)
            else:
                content_obj[key] = value
        translated_content.append(content_obj)
    return {
        'statusCode': 200,
        'result': json.dumps(translated_content)
    }


print(translate_tweet("2023-03-16 08:32:00.json"))
