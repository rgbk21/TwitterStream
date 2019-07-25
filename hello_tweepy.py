import tweepy
from pprint import pprint
import json

consumer_key = "wO8w6KENORTrUY3Kvcx8D7kwc"
consumer_secret = "YxsOqgHE0L6LFLTI3tvMmSzL4GkEpuUGxg5LMKbCSxduezGQqf"
access_token = "1129164193683386368-Clfi2rS7noy2jcrweFiPZadX3FeHmZ"
access_token_secret = "3DHtoRcQHQv4uWPpbDcXAbGswJCfWFGrVfo0kRT1aVtbi"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

user = api.get_user('DurarGaurav')
print(user.screen_name)
print(user.followers_count)
for friend in user.friends():
   print(friend.screen_name)
public_tweets = api.home_timeline()
print(len(public_tweets))
for tweet in public_tweets:
    print(tweet.text)

#override tweepy.StreamListener to add logic to on_status
class MyStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        print(status.text)

    def on_error(self, status):
        print(status)

    def on_data(self, data):

        all_data = json.loads(data)
        tweet = all_data["text"]
        username = all_data["user"]["screen_name"]

        print((username,tweet))
        pprint(all_data)

        return True

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
myStream.filter(track=['Pizza'], is_async=True)