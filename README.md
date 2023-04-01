# How to run
1. Create your own venv by running `python -m venv venv`
2. Activate your Python venv by running **MAC:** `source venv/bin/activate` or **Windows:** `source.bat`
3. Install the required libraries by running `pip install -r requirements.txt`
4. Rename `.env.example` to `.env` and add your own details into the file

# Infrastructure as Code
Builds the entire big data pipeline programmatically using terraform.Scraping topics are read from `topic.txt`
## How to run
1. [Install Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
2. In the terraform directory, rename `terraform.tfvars.example` to `terraform.tfvars` and add your own details into the file.
### For Mac & Linux Shell:
1. `make terraform init`
2. `make build_twitter_layer`
3. `make build_reddit_layer`
4. `make terraform_apply`
###  For Windows Users:
- Make your life easier, install [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) and follow the steps above