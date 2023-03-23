VENV_NAME = venv
TWITTER_DIR = twitter
REDDIT_DIR = reddit
TERRAFORM_FOLDER = terraform

.PHONY: build_twitter_layer build_reddit_layer 

$(TWITTER_DIR)/$(VENV_NAME)/bin/activate:
	$(MAKE) clean_twitter_venv
	cd $(TWITTER_DIR) && python3 -m venv $(VENV_NAME)

$(REDDIT_DIR)/$(VENV_NAME)/bin/activate:
	$(MAKE) clean_reddit_venv
	cd $(REDDIT_DIR) && python3 -m venv $(VENV_NAME)

build_twitter_layer: $(TWITTER_DIR)/$(VENV_NAME)/bin/activate
	. $(TWITTER_DIR)/venv/bin/activate
	pip install -r $(TWITTER_DIR)/requirements.txt
	cd $(TWITTER_DIR)/$(VENV_NAME)/lib*/python*/site-packages && zip -r ../../../../$(TWITTER_DIR)_scraper_layer.zip .
	
build_reddit_layer: $(REDDIT_DIR)/$(VENV_NAME)/bin/activate
	. $(REDDIT_DIR)/venv/bin/activate
	pip install -r $(REDDIT_DIR)/requirements.txt
	cd $(REDDIT_DIR)/$(VENV_NAME)/lib*/python*/site-packages && zip -r ../../../../$(REDDIT_DIR)_scraper_layer.zip .

clean_twitter_venv:
	rm -rf $(TWITTER_DIR)/$(VENV_NAME)

clean_reddit_venv:
	rm -rf $(REDDIT_DIR)/$(VENV_NAME)

