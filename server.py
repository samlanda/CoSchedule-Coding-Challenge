CLIENT_ID = "h-JtPgOEf-ptcQ"
CLIENT_SECRET = "oNwkmJJtbhB0sr3Lrgyvcj3OY6ClSw"
REDIRECT_URI = "http://localhost:65010/reddit_callback"

from flask import Flask, abort, request
import requests
import requests.auth
import json

def base_headers():
    return {"User-Agent": "cscc shl 0.01"}

app = Flask(__name__)
@app.route('/')


def homepage():
    text = '<a href="%s">Authenticate with reddit</a>'
    return text % make_authorization_url()

def make_authorization_url():
    from uuid import uuid4
    state = str(uuid4())
    params = {"client_id": CLIENT_ID,
                  "response_type": "code",
                          "state": state,
                          "redirect_uri": REDIRECT_URI,
                          "duration": "temporary",
                          "scope": "identity,vote,submit,read"}
    import urllib
    url = "https://ssl.reddit.com/api/v1/authorize?" + urllib.parse.urlencode(params)
    return url
    
@app.route('/reddit_callback')
def reddit_callback(): #Main Page
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    code = request.args.get('code')
    access_token = get_token(code)
    page = "Hi %s!<br>" % get_username(access_token)
    page += "<form action=\"http://localhost:65010/search\"><input type=\"text\" name=\"searchterm\" id=\"searchterm\" /><input type=\"submit\" name=\"search\" value=\"search\" /><input type=\"hidden\" id=\"token\" name=\"token\" value=\"%s\" /></form>" % access_token
    page += "<table><tr><th>Subreddit</th><th>Score</th><th>Title</th><th>Comments</th></tr>"
    page += "%s" % get_hot(access_token, code)
    page += "</table>"
    return page

def get_token(code): #Uses code to get access token
    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    post_data = {"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI}
    headers = base_headers()
    response = requests.post("https://ssl.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers = headers)
    token_json = response.json()
    return token_json["access_token"]

def get_username(access_token): #Gets username from access token
    headers = base_headers()
    headers.update({"Authorization": "bearer " + access_token})
    response = requests.get("https://oauth.reddit.com/api/v1/me", headers=headers)
    me_json = response.json()
    return me_json['name']

def get_hot(access_token, code): #Gets hot posts
    headers = base_headers()
    headers.update({"Authorization": "bearer " + access_token})
    response = requests.get("https://oauth.reddit.com/hot", headers=headers)
    
    page = ""
    for post in response.json()['data']['children']:
        page += "<tr><td>%s</td><td>%s</td><td><a href=\"%s\">%s</a></td><td><a href=http://localhost:65010/comment?token=%s&post=%s>Comments</a></td></tr>" % (post['data']['subreddit'], post['data']['score'], post['data']['url'], post['data']['title'],access_token, post['data']['name'])
    
    me_json = response.json()
    return page  

@app.route('/comment')
def comment(): #Page for showing top-level comments on a post
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    access_token = request.args.get('token')
    post = request.args.get('post')
    post=post[3:]
    page = "Hi %s!<br>" % get_username(access_token)
    page += "%s" % get_comments(access_token, post)
    #page += "</table>"
    return page

def get_comments(access_token, post): #gets the comments
    headers = base_headers()
    headers.update({"Authorization": "bearer " + access_token})
    link = "https://oauth.reddit.com/comments/%s" % post
    response = requests.get(link, headers=headers)
    page=""
    for comment in response.json()[1]['data']['children']:
        try: 
            page += "<p>%s</p>" % comment['data']['body']
        except:
            pass
        
    me_json = response.json()
    return page   

@app.route('/search')
def search(): #page for searching results
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    access_token = request.args.get('token')
    term = request.args.get('searchterm')
    page = "Hi %s!<br>" % get_username(access_token)
    page += "<table><tr><th>Subreddit</th><th>Score</th><th>Title</th><th>Comments</th></tr>"
    page += "%s" % get_results(access_token, term)
    page += "</table>"
    return page
    
def get_results(access_token, term): #gets search results
    headers = base_headers()
    headers.update({"Authorization": "bearer " + access_token})
    link = "https://oauth.reddit.com/search?q=%s" % term
    response = requests.get(link, headers=headers)
    page = ""
    for post in response.json()['data']['children']:
        page += "<tr><td>%s</td><td>%s</td><td><a href=\"%s\">%s</a></td><td><a href=http://localhost:65010/comment?token=%s&post=%s>Comments</a></td></tr>" % (post['data']['subreddit'], post['data']['score'], post['data']['url'], post['data']['title'],access_token, post['data']['name'])
    
    me_json = response.json()
    return page     
    
if __name__ == '__main__':
    app.run(debug=True, port=65010)