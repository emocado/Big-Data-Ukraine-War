import snscrape.modules.twitter as sntwitter
from datetime import datetime, timedelta


query = "ukraine war"
# Set the start and end dates for the search (in UTC timezone)
end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
start_date = end_date - timedelta(days=1)
tweets = []
for i, tweet in enumerate(sntwitter.TwitterSearchScraper(f"{query} since:{start_date.date()} until:{end_date.date()}").get_items()):
    tweets.append({
        'id': tweet.id,
        'date': tweet.date.strftime('%Y-%m-%d %H:%M:%S'),
        'content': tweet.rawContent
    })

print(tweets)