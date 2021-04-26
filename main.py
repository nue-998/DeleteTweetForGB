import json
import os
import sys
import oauth2 as oauth
from flask import Flask, render_template, request
import  psycopg2

app = Flask(__name__)

request_token_url = 'https://twitter.com/oauth/request_token'
access_token_url = 'https://twitter.com/oauth/access_token'
authenticate_url = 'https://twitter.com/oauth/authorize'
callback_url = 'https://delete-socialgames-tweets.herokuapp.com'
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']



@app.route("/")
def check_token():
    oauth_token = request.args.get('oauth_token', default="failed", type=str)
    oauth_verifier = request.args.get('oauth_verifier', default="failed", type=str)

    if oauth_token != "failed" and oauth_verifier != "failed":
        response = get_access_token(oauth_token, oauth_verifier).decode('utf-8')
        response = dict(parse_qsl(response))
        oauth_token = response['oauth_token']
        oauth_token_secret = response['oauth_token_secret']
        db_url = os.environ['DATABASE_URL']
        conn = psycopg2.connect(db_url, sslmode='require')
        cur = conn.cursor()
        cur.execute("insert into token (access_token, access_token_secret) values (%s, %s) on conflict do nothing", (oauth_token, oauth_token_secret))
        conn.commit()
        return render_template('cer.html', url="NoNeed")
    else:
        # リクエストトークンを取得する
        request_token = get_request_token()
        authorize_url = '%s?oauth_token=%s' % (authenticate_url, request_token)
        print(authorize_url)
        return render_template('cer.html', url=authorize_url, res="NoParams")

# 自分のツイート取得
def get_timeline(session):
    url = "https://api.twitter.com/1.1/statuses/user_timeline.json"

    params = {'count': 150, 'include_rts': 'false'}
    req = session.get(url, params=params)

    if req.status_code == 150:
        timeline = json.loads(req.text)
        return timeline
    else:
        print("ERROR: %d" % req.status_code)
        exit()

# グラブルから送信されたツイートの削除
def delete_gbf_tweets(tweets, session):
    for tweet in tweets:
        if tweet['source'] in source_strings:
            for word in search_words:
                if word in tweet['text']:
                    print(tweet['text'])
                    delete_tweet(tweet, session)
                    break

# 指定したツイートの削除
def delete_tweet(tweet, session):
    url = "https://api.twitter.com/1.1/statuses/destroy/"+tweet['id_str']+".json"
    req = session.post(url)
    if req.status_code == 200:
        print("delete success!")
    else:
        print("ERROR: %d" % req.status_code)