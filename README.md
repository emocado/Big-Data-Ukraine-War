# Building the pipeline
Builds the entire big data pipeline programmatically using terraform, an Infrastructure as Code framework. Scraping topics are read from `topic.txt`
## How to run
1. [Install Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
2. Run `aws configure` and define credentials for the AWS account you want to use. Ensure that the IAM user has the `AdministratorFullAccess` policy in order for terraform to build the required resources 
3. In the terraform directory, rename `terraform.tfvars.example` to `terraform.tfvars` and add your own details into the file.
### For Mac & Linux Shell:
1. `make terraform init`
2. `make build_twitter_layer`
3. `make build_reddit_layer`
4. `make terraform_apply`
###  For Windows Users:
- Make your life easier, install [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) and follow the steps above

# Testing locally
1. Create your own venv by running `python -m venv venv`
2. Activate your Python venv by running **MAC:** `source venv/bin/activate` or **Windows:** `source.bat`
3. Install the required libraries by running `pip install -r requirements.txt`
4. Rename `.env.example` to `.env` and add your own details into the file
