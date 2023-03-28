#########################################
### IMPORT LIBRARIES AND SET VARIABLES
#########################################

# Import Python modules
import sys
import logging
from datetime import datetime
import numpy as np

# Import pyspark modules
from pyspark.context import SparkContext
import pyspark.sql.functions as f
from pyspark.sql import Row

# Import glue modules
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job

# Import boto3 modules
import boto3

# Import neo4j modules
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# Initialize contexts and session
spark_context = SparkContext.getOrCreate()
glue_context = GlueContext(spark_context)
session = glue_context.spark_session
job = Job(glue_context)
job.init(args['JOB_NAME'], args)

# parameters 
glue_db = "project-database"
glue_post_tbl = "reddit_posts" 
glue_comment_tbl = "reddit_comments"
bucket = "tf-is459-ukraine-war-data"
s3_write_path = f"s3://{bucket}"
uri = "neo4j+s://a8ea8b44.databases.neo4j.io"
user = "neo4j"
password = "Kj_2iiLjGJuRVgW3vaQ3L8clptsLfhbSyFHTpIPxR3M"


s3 = boto3.client('s3')
obj = s3.get_object(Bucket=bucket, Key='topics.txt')
topics = obj['Body'].read().decode("utf-8").split("\n")
time_stamp = datetime.utcnow().strftime("%Y-%m-%d")


#########################################
### NEO4j Functions
#########################################
def create_post_relationships(tx, id, date, title, content, username, commentCount, score, subreddit):
    query = (
        "MERGE (p1:Post { id: $id, date: $date, title: $title, content: $content, username: $username, commentCount: $commentCount, score: $score, subreddit: $subreddit })"
        "MERGE (r1:Subreddit { name: $subreddit })"
        "MERGE (u1:User { username: $username })"
        "MERGE (p1)-[:POSTED_IN]->(r1)"
        "MERGE (p1)-[:POSTED_BY]->(u1)"
        "RETURN p1, r1, u1"
    )
    result = tx.run(query, id=id, date=date, title=title, content=content, username=username, commentCount=commentCount, score=score, subreddit=subreddit)
    try:
        return [{"p1": row["p1"]["id"], "r1": row["r1"]["name"], "u1": row["u1"]["username"]} for row in result]
    except ServiceUnavailable as exception:
        print("{query} raised an error: \n {exception}".format(
            query=query, exception=exception))
        raise
    

def create_comment_relationships(tx, id, date, content, username, score, post_id):
    query = (
        "MERGE (p1:Post { id: $postId })"
        "MERGE (u1:User { username: $username })"
        "MERGE (c1:Comment { id: $id, date: $date, content: $content, username: $username, score: $score, postId: $postId })"
        "MERGE (c1)-[:COMMENTED_ON]->(p1)"
        "MERGE (c1)-[:COMMENTED_BY]->(u1)"
        "RETURN c1, u1"
    )
    result = tx.run(query, id=id, date=date, content=content, username=username, score=score, postId=post_id)
    try:
        return [{"c1": row["c1"]["id"], "u1": row["u1"]["username"]} for row in result]
    except ServiceUnavailable as exception:
        print("{query} raised an error: \n {exception}".format(
            query=query, exception=exception))
        raise


def create_orchestrator(uri, user, password, posts, comments):
    data_base_connection = GraphDatabase.driver(uri=uri, auth=(user, password))
    with data_base_connection.session(database="neo4j") as session:
        # Write transactions allow the driver to handle retries and transient errors
        for post in posts:
            result = session.execute_write(create_post_relationships, post["id"], post["date"], post["title"], post["content"], post["username"], post["commentCount"], post["score"], post["subreddit"])
            print(f"Created: {result}")
        for comment in comments:
            result = session.execute_write(create_comment_relationships, comment["id"], comment["date"], comment["content"], comment["username"], comment["score"], comment["post_id"])
            print(f"Created: {result}")


def delete_all(tx):
    query = (
        "MATCH (n) DETACH DELETE n "
        "RETURN n"
    )
    result = tx.run(query)
    try:
        return [{"n": row["n"]["username"]} for row in result]
    # Capture any errors along with the query and data for traceability
    except ServiceUnavailable as exception:
        print("{query} raised an error: \n {exception}".format(
            query=query, exception=exception))


def delete_database(uri, user, password):
    data_base_connection = GraphDatabase.driver(uri=uri, auth=(user, password))
    with data_base_connection.session(database="neo4j") as session:
        # Write transactions allow the driver to handle retries and transient errors
        result = session.execute_write(delete_all)
        for row in result:
            print(f"Deleted: {row['n']}")

for query in topics:
    #########################################
    ### EXTRACT (READ DATA)
    #########################################
    dynamic_post_frame_read = glue_context.create_dynamic_frame.from_catalog(
        database = glue_db,
        table_name = glue_post_tbl,
        push_down_predicate =f"(topic == '{query}')"
    )
    dynamic_comment_frame_read = glue_context.create_dynamic_frame.from_catalog(
        database = glue_db,
        table_name = glue_comment_tbl,
        push_down_predicate =f"(topic == '{query}')"
    )
    
    # Convert dynamic frame to data frame to use standard pyspark functions
    data_post_frame = dynamic_post_frame_read.toDF().toPandas()
    data_comment_frame = dynamic_comment_frame_read.toDF().toPandas()
    
    # Extract out posts and comments of that timestamp
    data_post_frame = data_post_frame[data_post_frame['date'].str.startswith(time_stamp)]
    data_comment_frame = data_comment_frame[data_comment_frame['date'].str.startswith(time_stamp)]

    
    #########################################
    ### TRANSFORM (MODIFY DATA)
    #########################################
    
    def get_sentiment(text_list):
        # Initialize an empty list for storing sentiment results
        sentiments = []
        # Initialize an Amazon Comprehend client object with your region name (replace with your own region)
        comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
        # Split the text list into batches of 25 documents each (the maximum number of documents per request for Amazon Comprehend)
        batches = [[x[:4500] for x in text_list[i:i+25] if x] for i in range(0,len(text_list),25)]
        # Iterate over each batch and call the Amazon Comprehend API to analyze sentiment
        for i, batch in enumerate(batches):
            response = comprehend.batch_detect_sentiment(TextList=batch, LanguageCode='en')
            # Extract the sentiment scores from the response and append them to the sentiments list as Row objects 
            for item in response['ResultList']:
                index = i*len(batch) + item['Index']
                score = item['SentimentScore']
                sentiments.append({
                    "index": index, 
                    "Positive": score["Positive"], 
                    "Negative": score["Negative"], 
                    "Neutral": score["Neutral"], 
                    "Mixed": score["Mixed"]
                })
        # Return the sentiments list sorted by index 
        return sorted(sentiments, key=lambda x:x["index"])
    
    # Apply the UDF to your dataframe column and store the results in a new column
    data_post_frame = data_post_frame.replace("", np.nan)
    data_post_frame.dropna(inplace=True)
    post_sentiments = get_sentiment(data_post_frame.content.to_list())
    for key in post_sentiments[0].keys():
        data_post_frame[key] = [x[key] for x in post_sentiments]
    comment_sentiments = get_sentiment(data_comment_frame.content.to_list())
    for key in comment_sentiments[0].keys():
        data_comment_frame[key] = [x[key] for x in comment_sentiments]
        
    #########################################
    ### LOAD (WRITE DATA)
    #########################################
    
    create_orchestrator(uri, user, password, data_post_frame.to_dict('records'), data_comment_frame.to_dict('records'))
    
job.commit()