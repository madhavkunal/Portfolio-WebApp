import os
import requests
import feedparser
import openai
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='html')
CORS(app)
# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Set Flask secret key and API keys from environment variables
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    logging.error("Flask secret key is not set.")
openai.api_key = os.getenv('OPENAI_API_KEY')

# Define & Register the filter
def urlhost(url):
    return urlparse(url).hostname

app.jinja_env.filters['urlhost'] = urlhost

# Project 1. Hacker News Scraper Functions
@app.route('/hackernews-scraper', methods=['POST'])
def hackernews_scraper():
    try:
        post_count = 0
        hn_combined = []
        for page in range(1, 6):
            response = requests.get(f'https://news.ycombinator.com/news?p={page}')
            soup = BeautifulSoup(response.content, 'html.parser')
            titles = soup.select('.titleline > a')
            subtexts = soup.select('.subtext')

            for idx, title in enumerate(titles):
                subtext = subtexts[idx]
                points = subtext.select('.score')[0].get_text() if subtext.select('.score') else '0 points'
                author = subtext.select('.hnuser')[0].get_text() if subtext.select('.hnuser') else 'Unknown'
                posted = subtext.select('.age > a')[0].get_text() if subtext.select('.age > a') else 'Unknown time'
                comments = subtext.select('a')[-1].get_text().split()[0] if subtext.select('a')[-1].get_text().split()[0] != 'discuss' else '0'
                comments_url = subtext.select('a')[-1]['href'] if comments != '0' else ''

                title_url = title['href'] if title['href'].startswith('http') else 'https://news.ycombinator.com/' + title['href']

                item = {
                    'Title': title.get_text(),
                    'Link': title_url,
                    'Author': author,
                    'Posted': posted,
                    'Points': points,
                    'Comments': comments,
                    'Comments_URL': 'https://news.ycombinator.com/' + comments_url if comments_url else ''
                }
                hn_combined.append(item)
                post_count += 1
                if post_count >= 8:
                    return jsonify({'html': render_template('hn_results.html', hn_combined=hn_combined)})
        return jsonify({'html': render_template('hn_results.html', hn_combined=hn_combined)})
    except Exception as e:
        return jsonify({'error': str(e)})
    
# Project 2. ChatGPT 4o Functions
def get_chat_response(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": message}]
        )
        return response.choices[0].message['content']
    except Exception as e:
        logging.error(f"Failed to get response from OpenAI: {str(e)}")
        return None

# OpenAI GPT-4o Route
@app.route('/api/openai', methods=['POST'])
def api_openai():
    data = request.get_json()
    user_input = data.get('question')
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400
    response = get_chat_response(user_input)
    if response:
        return jsonify({'answer': response})
    else:
        return jsonify({'error': 'Failed to get response from OpenAI'}), 500

# Substack Blog Posts Page Route
@app.route("/get-substack-posts", methods=['GET'])
def get_substack_posts():
    SUBSTACK_USERNAME = 'madhavkunal'
    feed_url = f"https://{SUBSTACK_USERNAME}.substack.com/feed"
    response = requests.get(feed_url)
    feed = feedparser.parse(response.content)
    post_data = []
    default_image_url = url_for('static', filename='img/substack/Substack.png', _external=True)

    for post in feed.entries:
        soup = BeautifulSoup(post.content[0].value, features="html.parser")  # Ensure you're parsing the correct part of the feed
        
        image_tag = soup.find('img')
        image_url = image_tag['src'] if image_tag else default_image_url

        content_text = soup.get_text()
        content_snippet = content_text[:445] + ' ...' if len(content_text) > 450 else content_text
        
        post_data.append({
            'title': post.title,
            'date': post.published,
            'content': content_snippet,
            'url': post.link,
            'imageUrl': image_url
        })

    return jsonify(post_data)

# Static Routes and Main App Configuration
@app.route('/')
def home():
    return render_template('index.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/portfolio")
def portfolio():
    return render_template('portfolio.html')

@app.route("/blog")
def blog():
    return render_template('blog.html')

@app.route('/<path:filename>')
def serve_static(filename):
    static_dir = os.path.join(app.root_path, 'static')
    return send_from_directory(static_dir, filename)

application = app

if __name__ == '__main__':
    application.run(debug=True)


# To run program and see website in localhost: http://127.0.0.1:5000/:
# 1. Open Visual Studio Code Application as Administrator
# 2. cd .\Section19_WebDevelopmentWithPython\
# 3. cd cd .\web_server_venv\
# 4. Set-ExecutionPolicy RemoteSigned  (Requires Login VSCode as Admin)
# 5. Get-ExecutionPolicy #RemoteSigned (Requires Login VSCode as Admin)
# 6. To activate Virtual Environment, Run the following cmd:  'Scripts\activate'        
# 7. python server.py  [NOT python3 server.py]          