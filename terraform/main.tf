provider "aws" {
    region = "us-east-1"
}

data "archive_file" "twitter_zip" {
    type = "zip"
    source_file = "../twitter/lambda_function.py"
    output_path = "../twitter/lambda_function.zip"
  
}

data "aws_iam_policy_document" "lambda_policy" {
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

resource "aws_s3_bucket" "is459-project" {
    bucket = "is459-project"
    acl = "private"
}

resource "aws_iam_role" "lambda_iam" {
    name = "lambda_iam"
    assume_role_policy = data.aws_iam_policy_document.lambda_policy.json
}

resource "aws_lambda_function" "twitter_scraper" {
    description = "An Amazon S3 trigger that retrieves metadata for the object that has been updated."
    runtime = var.lambda_runtime
    handler = "lambda_function.lambda_handler"
    function_name = "twitter_scraper"
    filename = data.archive_file.twitter_zip.output_path
    source_code_hash = data.archive_file.twitter_zip.output_base64sha256
    
    role = aws_iam_role.lambda_iam.arn
}


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
# resource "aws_lambda_function" "reddit_scraper" {
#     runtime = local.lambda_runtime
# }

# resource "aws_vpc" "is459-vpc" {
#     cidr_block = "10.0.0.0/16"
#     tags = {
#         Name = "is459-vpc"
#     }
# }