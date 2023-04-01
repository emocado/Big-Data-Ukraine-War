# How to run
1. Create your own venv by running `python -m venv venv`
2. Activate your Python venv by running **MAC:** `source venv/bin/activate` or **Windows:** `source.bat`
3. Install the required libraries by running `pip install -r requirements.txt`
4. Rename `.env.example` to `.env` and add your own details into the file

# Infrastructure as Code
Build the entire big data pipeline programmatically using terraform
- Reads topic.txt for topics to scrape
- Prerequisite: [Terraform is installed](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
### Run for mac
1. `make terraform init` 
2. `terraform apply`
### Run for windows 
1. `cd terraform`
2. `terraform init`
3. `terraform apply`