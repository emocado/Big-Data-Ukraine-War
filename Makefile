VENV_NAME = venv
TWITTER_DIR = twitter
REDDIT_DIR = reddit
TERRAFORM_FOLDER = terraform

.PHONY: build_twitter_layer build_reddit_layer 

$(TWITTER_DIR)/layer:
	$(MAKE) clean_twitter_layer
	cd $(TWITTER_DIR) && mkdir python

$(REDDIT_DIR)/layer:
	$(MAKE) clean_twitter_layer
	cd $(REDDIT_DIR) && mkdir python

terraform_apply:
	cd terraform && terraform apply

build_twitter_layer: $(TWITTER_DIR)/layer
	cd $(TWITTER_DIR) && pip install -r requirements.txt -t python/
	cd $(TWITTER_DIR)&& zip -r layer.zip python

build_reddit_layer: $(REDDIT_DIR)/layer
	cd $(REDDIT_DIR) && pip install -r requirements.txt -t python/
	cd $(REDDIT_DIR)&& zip -r layer.zip python
	
clean_twitter_layer:
	rm -rf $(TWITTER_DIR)/python

clean_reddit_layer:
	rm -rf $(REDDIT_DIR)/pytho