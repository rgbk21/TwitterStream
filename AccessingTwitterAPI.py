import tweepy
import os
import numpy as np
import pandas as pd
import zipfile
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from tweepy.streaming import StreamListener
from tweepy import Stream
from tweepy import API
from tweepy import Cursor
from textblob import TextBlob
import re  # reges library
from credentials import consumer_key
from credentials import consumer_secret
from credentials import access_token
from credentials import access_token_secret

from pprint import pprint
import json


# # # # TWITTER CLIENT # # # #
class TwitterClient():
    # twitter_user=None is a default specification of the argument to the function. If no parameter is specified then the
    # code just returns the information of the self user.
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)
        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    # num_tweets is the number of tweets that you want to extract from the user's timeline
    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_friend_list(self, num_friends):
        friend_list = []
        # the id argument in the Cursor object helps us specify the user for which we want to pull the data
        for friend in Cursor(self.twitter_client.friends, id=self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list

    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline, id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets


# # # # TWITTER AUTHENTICATER # # # #
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        return auth


# # # # TWITTER STREAMER # # # #
class TwitterStreamer():
    """
    Class for streaming and processing live tweets.
    """

    def __init__(self):  # constructor?
        self.twitter_authenticator = TwitterAuthenticator()

    # hash_tag_list is the words that you will be using to filter the tweets
    def stream_tweets(self, fetched_tweets_filename, hash_tag_list):
        # This handles Twitter authentication and the connection to Twitter Streaming API
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_authenticator.authenticate_twitter_app()
        stream = Stream(auth, listener)

        # This line filter Twitter Streams to capture data by the keywords:
        stream.filter(track=hash_tag_list)


# # # # TWITTER STREAM LISTENER # # # #
class TwitterListener(StreamListener):
    """
    This is a basic listener that just prints received tweets to stdout.
    """

    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):
        try:
            print(data)
            with open(fetched_tweets_filename, 'a') as tf:
                tf.write(data)
                statinfo = os.stat(fetched_tweets_filename)
                if statinfo.st_size > 1e+9:
                    print("File Size Exceeded")
                    zip_file = zipfile.ZipFile(str(fetched_tweets_filename) + ".zip", 'w')
                    zip_file.write(fetched_tweets_filename, compress_type=zipfile.ZIP_DEFLATED)
                    zip_file.close()
                    os.remove(fetched_tweets_filename)
                    print("Creating a new file and direct the stream towards it")
                    return False
            return True
        except BaseException as e:
            print("Error on_data %s" % str(e))
        return True

    def on_error(self, status):
        if status == 420:
            # Returning false on_data method in case the rate_limit is exceeded. This will send a 420 error from Twitter
            print("Warning: rate_limit reached for Twitter")
            return False  # KILL STREAM
        print(status)


class TweetAnalyzer():
    """
    Functionality for analyzing and categorizing content from tweets
    """

    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))
        if analysis.sentiment.polarity > 0:
            return 1
        elif analysis.sentiment.polarity == 0:
            return 0
        else:
            return -1

    def tweets_to_dataframe(self, tweets):
        # tweet.text extracts the text from each tweet in tweets
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=["tweets"])
        # df["id"] creates a new column in the dataframe called "id"
        # So this line of code: looks at the tweets object passed as the argument, cycles through each tweet in tweets, copies the id of the tweet, stores it in an array, converts it into a numpy array, adds it to the pd dataframe under the "id" column
        df["id"] = np.array([tweet.id for tweet in tweets])
        df["len"] = np.array([len(tweet.text) for tweet in tweets])
        df["creation"] = np.array([tweet.created_at for tweet in tweets])
        df["retweet_count"] = np.array([tweet.retweet_count for tweet in tweets])
        df["favorite_count"] = np.array([tweet.favorite_count for tweet in tweets])
        df["retweeted"] = np.array([tweet.retweeted for tweet in tweets])
        return df


if __name__ == '__main__':
    # Authenticate using config.py and connect to Twitter Streaming API.
    # hash_tag_list=['#JeffreyEpsteinDead', '#EpsteinSuicide', '#EpsteinMurder', '#ClintonBodyCount']
    hash_tag_list = ['#HongKongAirport', '#HongKong', 'Hong Kong']
    count = 0
    fetched_tweets_filename = "tweets_HK_" + str(count) + "_.txt"
    # Uncomment the below 2 lines for Streaming Tweets to the file
    # twitter_streamer = TwitterStreamer()#Creates an object of the class TwitterStreamer
    # twitter_streamer.stream_tweets(fetched_tweets_filename, hash_tag_list)

    # while True:
    #     count = count + 1
    #     fetched_tweets_filename = "tweets_HK_" + str(count) + "_.txt"
    #     twitter_streamer.stream_tweets(fetched_tweets_filename, hash_tag_list)
    # gauth = GoogleAuth()
    # gauth.LocalWebserverAuth()
    # drive = GoogleDrive(gauth)

    # Uncomment the below lines for getting tweets of a specific user:
    # twitter_client = TwitterClient("CppCon")
    twitter_client = TwitterClient()  # creating an object from TwitterClient class
    api = twitter_client.get_twitter_client_api()
    tweet_analyzer = TweetAnalyzer()  # Creating an object from TweetAnalyzer class
    # api.user_timeline is a function that is provided by the twitter API. It is not a function that we have written.
    # Check: http://docs.tweepy.org/en/v3.8.0/api.html for more examples of such functions

    # This code will get the latest "count" number of tweets from the user "screen_name".
    # It will build a dataframe with the columns specified in the tweets_to_dataframe method
    # it will calculate the sientiment of the tweet and add it to the created datatframe
    # And then finally print the dataframe to the console
    # tweets = api.user_timeline(screen_name="DurarGaurav", count=20)

    # print("Starting Printing individual tweet objects from User")
    # for tweet in tweets:
    #     print(tweet._json, sep="")
    # print("Completed Printing individual tweet objects from User")

    # Use the following Code to get the user related details like follower_count, friend_count, user_description
    test = api.lookup_users(user_ids=['1090715513586679813',
                                      '25073877',
                                      '60783724',
                                      '4513039632',
                                      '30188594',
                                      '60113110',
                                      '1639530362',
                                      '3228637992',
                                      '49616273',
                                      '471516779',
                                      '18956073',
                                      '1093705708619681797',
                                      '347927511',
                                      '4828068038',
                                      '18798768',
                                      '809887021',
                                      '757893380',
                                      '32626129',
                                      '494974123',
                                      '1339835893',
                                      '1877831',
                                      '138141969',
                                      '72345868',
                                      '252751061',
                                      '87775422',
                                      '1115874631',
                                      '592730371',
                                      '76347918',
                                      '112551613',
                                      '303862998',
                                      '872683897',
                                      '19739126',
                                      '109579590',
                                      '896778691954434048',
                                      '15745368',
                                      '774375759284756480',
                                      '1105235739355291649',
                                      '173162992',
                                      '1117012713329152000',
                                      '45808079',
                                      '2466036350',
                                      '62093225',
                                      '1077127237999063040',
                                      '1186149476',
                                      '951302891708583936',
                                      '1053329245919940608',
                                      '21366823',
                                      '292929271',
                                      '1080894931311431682',
                                      '16288136',
                                      '23922797',
                                      '1330457336',
                                      '27284203',
                                      '21439144',
                                      '2836421',
                                      '55734987',
                                      '1073786153910853632',
                                      '30354991',
                                      '471677441',
                                      '50943008',
                                      '748365116769452032',
                                      '27000730',
                                      '1079776144524754944',
                                      '7493052',
                                      '4914384040',
                                      '1095500352651173888',
                                      '41634520',
                                      '231712188',
                                      '930552552302792705',
                                      '1144711684013076483',
                                      '759251',
                                      '807095',
                                      '632962034',
                                      '3071162052',
                                      '103280363',
                                      '3384104129',
                                      '563016943',
                                      '38495835',
                                      '65172298',
                                      '379620203',
                                      '525658038',
                                      '1001165088697585664',
                                      '15764644',
                                      '34713362',
                                      '409062401',
                                      '17494010',
                                      '28785486',
                                      '380648579',
                                      '256360738',
                                      '948464246064427008',
                                      '568400331',
                                      '893680236',
                                      '6440792',
                                      '820354372827758592',
                                      '338985020',
                                      '928444328',
                                      '240107748',
                                      '1048214603077808128',
                                      '873115441303924736'
                                      ])
    df = pd.DataFrame(data=test)
    df["screen_name"] = np.array([user.screen_name for user in test])
    df["user.id_str"] = np.array([user.id_str for user in test])
    df["user.followers_count"] = np.array([user.followers_count for user in test])
    df["user.friends_count"] = np.array([user.friends_count for user in test])
    df["user.verified"] = np.array([user.verified for user in test])
    df["user.description"] = np.array([user.description for user in test])
    # print(df[["user.description"]].to_string())
    print(df[["screen_name", "user.id_str", "user.followers_count", "user.friends_count", "user.verified"]].to_string())
    index = 0
    for user in test:
        #     print("user.screen_name: " + user.screen_name)
        #     print("user.id_str: " + user.id_str)
        print("index: "+ str(index) + ": " + user.description)
        index += 1
    #     print("followers_count: " + str(user.followers_count))
    #     print("friends_count: " + str(user.friends_count))
    #     print("user.verified: " + str(user.verified))
    #     print("************************************************")

    # df = tweet_analyzer.tweets_to_dataframe(tweets)
    # Adding the sentiment to the dataframe
    # df["sentiment"] = np.array([tweet_analyzer.analyze_sentiment(tweet) for tweet in df["tweets"]])

    # print(dir(tweets[0]))#prints outs the attributes that we can use for each tweet
    # print(df.head(10))#print out the first 10 elements in the dataframe
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
    #     print(df)

    # print(tweets)
    # print(twitter_client.get_friend_list(10))
