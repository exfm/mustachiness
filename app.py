from flask import Flask, render_template, jsonify, request, json
from exfm import ExfmClient
from werkzeug.routing import BaseConverter
from werkzeug.urls import url_fix
import urllib
import urllib2
from collections import OrderedDict

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


def search_en():
    params = [
        ('api_key', 'N6E4NIOVYMTHNDM8J'),
        ('artist', request.values.get('artist')),
        ('title', request.values.get('title')),
        ('bucket', 'audio_summary'),
        ('bucket', 'song_hotttnesss'),
    ]
    fp = urllib2.urlopen("http://developer.echonest.com/api/v4/song/search?%s" % urllib.urlencode(params))
    data = fp.read()
    fp.close()
    return json.loads(data)


def song_profile(*id):
    params = [('api_key', 'N6E4NIOVYMTHNDM8J')]
    [params.append(('id', _)) for _ in id]

    fp = urllib2.urlopen("http://developer.echonest.com/api/v4/song/profile?%s" % urllib.urlencode(params))
    data = fp.read()
    fp.close()
    return json.loads(data)


@app.route('/api/data')
def api_data():
    song = search_en()['response']['songs'][0]
    analysis_url = song['audio_summary']['analysis_url']
    fp = urllib2.urlopen(analysis_url)
    data = json.loads(fp.read())
    fp.close()
    song['loudness'] = OrderedDict([(item['start'], item['loudness_max'])
         for item in data['segments']])

    return jsonify({'song': song})
