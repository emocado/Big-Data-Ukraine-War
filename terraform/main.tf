provider "aws" {
    region = "us-east-1"
}

/*
*   Preparing lambda function file for twitter scraper
*/
data "archive_file" "twitter_zip" {
    type = "zip"
    source_file = "../twitter/lambda_function.py"
    output_path = "../twitter/lambda_function.zip"
}


/*
* Start of S3 bucket setup
* Create bucket called is459-project
* Add topics.txt into bucket, used to define topics to scrape
*/
resource "aws_s3_bucket" "is459-project" {
    bucket = var.data_bucket
}

resource "local_file" "topic_file" {
  content  = file("topics.txt")
  filename = "topics.txt"
}

resource "aws_s3_object" "topic_object" {
    bucket = var.data_bucket
    key = "topics.txt"
    source = local_file.topic_file.filename
}

/*
* End of S3 bucket setup
*/


/*
* Start of scraper policies and role definition
*/
data "aws_iam_policy_document" "scraper_policy" {
    statement {
        sid = ""
        effect = "Allow"

        principals {
            identifiers = ["lambda.amazonaws.com"]
            type = "Service"
        }
        actions = ["sts:AssumeRole"]
    } 
}


resource "aws_iam_role" "scraper_role" {
    name = "scraper_role"
    assume_role_policy = data.aws_iam_policy_document.scraper_policy.json
}


resource "aws_iam_role_policy_attachment" "scraper_role_lambda_basic_policy_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" # Attach the basic Lambda execution role
  role       = aws_iam_role.scraper_role.name
}


resource "aws_iam_role_policy_attachment" "scraper_role_s3_full_access_policy_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess" # Attach the Amazon S3 full access policy
  role       = aws_iam_role.scraper_role.name
}

resource "aws_iam_role_policy_attachment" "scraper_role_glue_service_policy_attachment" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole" # Attach the AWS Glue service role policy
  role       = aws_iam_role.scraper_role.name
}

/*
* End of scraper policies and role definition
*/

/*
* Start of Lambda function definition for twitter scraper
*/

resource "aws_lambda_function" "twitter_scraper" {
    description = "An Amazon S3 trigger that retrieves metadata for the object that has been updated."
    runtime = var.lambda_runtime
    handler = "lambda_function.lambda_handler"
    function_name = "twitter_scraper"
    filename = data.archive_file.twitter_zip.output_path
    source_code_hash = data.archive_file.twitter_zip.output_base64sha256
    
    role = aws_iam_role.scraper_role.arn
    layers = ["arn:aws:lambda:us-east-1:196888521910:layer:snscrape-only:3"]
    timeout = 300
}

/*
* End of Lambda function definition for twitter scraper
*/


/*
* Start of Scraper Lambda Trigger definition 
*/
resource "aws_cloudwatch_event_rule" "scraper_trigger_15_minutes" {
    name = "scraper_trigger_15_minutes"
    description = "Triggers every 15 minutes"

    schedule_expression = "rate(15 minutes)" 
}

resource "aws_cloudwatch_event_target" "cloudwatch_lambda_target" {
    rule = aws_cloudwatch_event_rule.scraper_trigger_15_minutes.name
    arn = aws_lambda_function.twitter_scraper.arn
    target_id = "twitter_scraper"
}


resource "aws_lambda_permission" "cloudwatch_lambda_trigger" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.twitter_scraper.function_name
    principal =  "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.scraper_trigger_15_minutes.arn
}
/*
* End of Scraper Lambda Trigger definition 
*/
