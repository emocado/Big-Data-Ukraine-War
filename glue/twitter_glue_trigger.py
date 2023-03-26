import boto3
print('Loading function')

def lambda_handler(_event, _context):
    glue = boto3.client('glue')
    gluejobname = "twitter-comprehend-glue-job-v2"

    try:
        runId = glue.start_job_run(JobName=gluejobname)
        status = glue.get_job_run(JobName=gluejobname, RunId=runId['JobRunId'])
        print("Job Status : ", status['JobRun']['JobRunState'])
    except Exception as e:
        print(e)
        raise