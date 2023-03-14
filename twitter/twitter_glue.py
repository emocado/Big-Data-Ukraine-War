#########################################
### IMPORT LIBRARIES AND SET VARIABLES
#########################################

# Import Python modules
import sys
from datetime import datetime

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


## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# Initialize contexts and session
spark_context = SparkContext.getOrCreate()
glue_context = GlueContext(spark_context)
session = glue_context.spark_session
job = Job(glue_context)
job.init(args['JOB_NAME'], args)

# Parameters
bucket = "wklee-is459"
s3_write_path = f"s3://{bucket}/project_write"
folder="project/"


#########################################
### EXTRACT (READ DATA)
#########################################
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket)
objects = list(bucket.objects.filter(Prefix=folder))
objects.sort(key=lambda x: x.last_modified)
latest_file = objects[-1].key

dynamic_frame_read = glue_context.create_dynamic_frame_from_options(
    connection_type="s3", format="json",
    connection_options={"paths": [f"s3://{bucket}/{latest_file}"]},
    format_option={"jsonPath": "$[*]", "multiline": True})

# Convert dynamic frame to data frame to use standard pyspark functions
data_frame = dynamic_frame_read.toDF().toPandas()


#########################################
### TRANSFORM (MODIFY DATA)
#########################################

def get_sentiment(text_list):
    # Initialize an empty list for storing sentiment results
    sentiments = []
    # Initialize an Amazon Comprehend client object with your region name (replace with your own region)
    comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
    # Split the text list into batches of 25 documents each (the maximum number of documents per request for Amazon Comprehend)
    batches = [text_list[i:i+25] for i in range(0,len(text_list),25)]
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
sentiments = get_sentiment(data_frame.content.to_list())
for key in sentiments[0].keys():
    data_frame[key] = [x[key] for x in sentiments]

#########################################
### LOAD (WRITE DATA)
#########################################

data_frame.to_csv(f"{s3_write_path}/ouput2.csv")

job.commit()