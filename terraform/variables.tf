variable "lambda_runtime" {
    type = string
    default = "python3.9"
}

variable "data_bucket" {
    type = string
    default = "tf-is459-ukraine-war-data"
}

variable "REDDIT_CLIENT_ID" {}
variable "REDDIT_CLIENT_SECRET" {}
variable "REDDIT_PASSWORD" {}
variable "REDDIT_USERNAME" {}
variable "REDDIT_USER_AGENT" {}