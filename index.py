import http.client
import json
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# API Connection Setup
conn_user = http.client.HTTPSConnection("twitter-api47.p.rapidapi.com")
headers = {
    'x-rapidapi-key': "5d54c973b7msh2418c169d4909b0p1e5362jsn1123fc1cd8ae",
    'x-rapidapi-host': "twitter-api47.p.rapidapi.com"
}
conn_tweet = http.client.HTTPSConnection("twitter-api47.p.rapidapi.com")


def create_directory(path):
    os.makedirs(path, exist_ok=True)
    return path


def download_profile_image(profile_image_url, username):
    try:
        if profile_image_url:
            profile_images_dir = create_directory(os.path.join(os.getcwd(), username, f"{username}_profile"))
            response = requests.get(profile_image_url)
            if response.status_code == 200:
                filepath = os.path.join(profile_images_dir, "profile_pic.jpg")
                with open(filepath, 'wb') as file:
                    file.write(response.content)
    except Exception as e:
        print(f"Error downloading profile image: {e}")


def download_post_images(tweets, username):
    try:
        tweets_images_dir = create_directory(os.path.join(os.getcwd(), username, f"{username}_posts"))
        for index, tweet in enumerate(tweets):
            media_urls = tweet.get("media", [])
            for img_url in media_urls:
                try:
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        filename = f"{username}_post_{index}.jpg"
                        filepath = os.path.join(tweets_images_dir, filename)
                        with open(filepath, 'wb') as file:
                            file.write(response.content)
                except Exception as e:
                    print(f"Error downloading tweet image {img_url}: {e}")
    except Exception as e:
        print(f"Error downloading post images: {e}")


def save_post_captions_to_json(tweets, username):
    try:
        captions_dir = create_directory(os.path.join(os.getcwd(), username, f'{username}_captions'))
        captions_filepath = os.path.join(captions_dir, "captions.json")
        captions = [{"Caption": tweet.get("text", "No caption available")} for tweet in tweets]
        with open(captions_filepath, "w", encoding="utf-8") as json_file:
            json.dump(captions, json_file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving post captions to JSON: {e}")


def fetch_user_details(username):
    try:
        conn_user.request("GET", f"/v2/user/by-username?username={username}", headers=headers)
        res = conn_user.getresponse()
        if res.status != 200:
            return None, None
        data = json.loads(res.read().decode("utf-8"))
        selected_fields = {
            'Username': data['legacy'].get('name'),
            'Name': data['legacy'].get('screen_name'),
            'Bio': data['legacy'].get('description'),
            'Followers': data['legacy'].get('normal_followers_count'),
            'Following': data['legacy'].get('friends_count'),
            'Verified': data.get('is_blue_verified'),
            'AccountPrivacy': data['verification_info'].get('is_identity_verified'),
            'default_profile_image': data['legacy'].get('profile_banner_url'),
            'NumberOfPosts': data['legacy'].get('media_count'),
            'profile_image_url_https': data['legacy'].get('profile_banner_url'),
            "Socialmediasite": "Twitter",
        }
        return data, selected_fields
    except Exception as e:
        print(f"Error fetching user details: {e}")
        return None, None


def fetch_user_tweets(username, user_id, count=10):
    try:
        conn_tweet.request("GET", f"/v2/user/tweets?userId={user_id}&count={count}", headers=headers)
        res = conn_tweet.getresponse()
        if res.status != 200:
            return None
        return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching tweets: {e}")
        return None


def process_tweets(tweets_raw_data):
    try:
        extracted_tweets = []
        for tweet_entry in tweets_raw_data.get("tweets", []):
            legacy = tweet_entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {}).get("legacy", {})
            tweet_text = legacy.get("full_text", "No text available")
            media = legacy.get("extended_entities", {}).get("media", [])
            media_urls = [item.get("media_url_https") for item in media if item.get("type") == "photo"]
            extracted_tweets.append({"text": tweet_text, "created_at": legacy.get("created_at"), "media": media_urls})
        return extracted_tweets
    except Exception as e:
        print(f"Error processing tweets: {e}")
        return []


@app.route('/api/detect', methods=['POST'])
def detect_x():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username is required.'}), 400
    try:
        raw_user_details, processed_user_details = fetch_user_details(username)
        if raw_user_details and processed_user_details:
            user_id = raw_user_details.get("rest_id")
            tweets_raw = fetch_user_tweets(username, user_id, count=10)
            processed_tweets = process_tweets(tweets_raw) if tweets_raw else []
            response_data = {
                "ProfileInfo": processed_user_details,
                "Tweets": processed_tweets
            }
            return jsonify(response_data), 200
        else:
            return jsonify({'error': 'Failed to fetch user details.'}), 500
    except Exception as e:
        return jsonify({'error': f"Unexpected error: {str(e)}"}), 500
