from flask import Flask, render_template, jsonify
from exfm import ExfmClient
from werkzeug.routing import BaseConverter
from werkzeug.urls import url_fix

app = Flask(__name__)

exfm = ExfmClient()


class UrlConverter(BaseConverter):
    regex = '[^/].*?'
    is_greedy = True
    weight = 50

    def to_python(self, value):
        return url_fix(value).replace('http:///', 'http://')


app.url_map.converters['url'] = UrlConverter


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/api/search/<q>')
def api_search(q):
    results = exfm.get_song_search_results(q)
    return jsonify(results)


@app.route('/api/data/<url:url>')
def api_data(url):
    return jsonify({'url': url})
