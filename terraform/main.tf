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

data "archive_file" "reddit_zip" {
    type = "zip"
    source_file = "../reddit/lambda_function.py"
    output_path = "../reddit/lambda_function.zip"
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
* Start of Lambda layer definition
*/
resource "aws_lambda_layer_version" "twitter_scraper_layer" {
    layer_name = "twitter-scraper"
    compatible_runtimes = [
        "python3.7",
        "python3.8",
        "python3.9"
    ]
    filename = "../twitter/layer.zip"
    description = "Layer that includes boto3 and snscrape"
}


resource "aws_lambda_layer_version" "reddit_scraper_layer" {
    layer_name = "reddit-scraper"
    compatible_runtimes = [
        "python3.7",
        "python3.8",
        "python3.9"
    ]
    filename = "../reddit/layer.zip"
    description = "Layer that includes boto3 and praw"
}

/*
* End of Lambda layer definition
*/



/*
* Start of Lambda function definition for twitter scraper
*/

resource "aws_lambda_function" "twitter_scraper" {
    description = "Twitter scraper that scrapes tweets based on topics.txt"
    runtime = var.lambda_runtime
    handler = "lambda_function.lambda_handler"
    function_name = "twitter_scraper"
    filename = data.archive_file.twitter_zip.output_path
    source_code_hash = data.archive_file.twitter_zip.output_base64sha256
    
    role = aws_iam_role.scraper_role.arn
    layers = [aws_lambda_layer_version.twitter_scraper_layer.arn]
    timeout = 300
}

resource "aws_lambda_function" "reddit_scraper" {
    description = "Reddit scraper that scrapes tweets based on topics.txt"
    runtime = var.lambda_runtime
    handler = "lambda_function.lambda_handler"
    function_name = "reddit_scaper"
    filename = data.archive_file.reddit_zip.output_path
    source_code_hash = data.archive_file.reddit_zip.output_base64sha256
    
    role = aws_iam_role.scraper_role.arn
    layers = [aws_lambda_layer_version.reddit_scraper_layer.arn]
    timeout = 300
    environment {
      variables = {
        REDDIT_CLIENT_ID = var.REDDIT_CLIENT_ID
        REDDIT_CLIENT_SECRET = var.REDDIT_CLIENT_SECRET
        REDDIT_PASSWORD = var.REDDIT_PASSWORD
        REDDIT_USERNAME = var.REDDIT_USERNAME
        REDDIT_USER_AGENT = var.REDDIT_USER_AGENT
      }
    }
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

resource "aws_cloudwatch_event_target" "cloudwatch_lambda_target_twitter" {
    rule = aws_cloudwatch_event_rule.scraper_trigger_15_minutes.name
    arn = aws_lambda_function.twitter_scraper.arn
    target_id = "twitter_scraper"
}


resource "aws_lambda_permission" "cloudwatch_lambda_trigger_twitter" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.twitter_scraper.function_name
    principal =  "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.scraper_trigger_15_minutes.arn
}

resource "aws_cloudwatch_event_target" "cloudwatch_lambda_target_reddit" {
    rule = aws_cloudwatch_event_rule.scraper_trigger_15_minutes.name
    arn = aws_lambda_function.reddit_scraper.arn
    target_id = "reddit_scraper"
}


resource "aws_lambda_permission" "cloudwatch_lambda_trigger_reddit" {
    statement_id = "AllowExecutionFromCloudWatch"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.reddit_scraper.function_name
    principal =  "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.scraper_trigger_15_minutes.arn
}
/*
* End of Scraper Lambda Trigger definition 
*/