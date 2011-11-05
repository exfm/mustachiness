from flask import Flask, render_template, jsonify, request, json
from exfm import ExfmClient
from werkzeug.routing import BaseConverter
from werkzeug.urls import url_fix
import urllib
import urllib2
from collections import OrderedDict
import redis

CACHING = True

app = Flask(__name__)

exfm = ExfmClient()

_redis = None


def get_redis():
    global _redis
    if not _redis:
        _redis = redis.Redis(
            db=12
        )

    return _redis


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


@app.route('/api/latest')
def api_latest():
    r = get_redis()
    ids = r.lrange('latest_staches', request.values.get('start', 0), request.values.get('results', 20))
    print ids
    pipe = r.pipeline()
    [pipe.get('cache:data:%s' % _) for _ in ids]
    res = pipe.execute()
    print res
    return jsonify({'staches': [json.loads(x) for x in res]})


def extract(q):
    params = [
        ('api_key', 'N6E4NIOVYMTHNDM8J'),
        ('text', q)
    ]
    fp = urllib2.urlopen("http://developer.echonest.com/api/v4/artist/extract?%s" % urllib.urlencode(params))
    data = fp.read()
    fp.close()
    resp = json.loads(data)
    artist = resp['response']['artists'][0]['name'].lower()
    title = q.lower().replace(artist.lower(), '')

    return artist.strip(), title.strip()


def search_en():
    if request.values.get('q'):
        artist, title = extract(request.values.get('q'))
    else:
        artist = request.values.get('artist')
        title = request.values.get('title')

    params = [
        ('api_key', 'N6E4NIOVYMTHNDM8J'),
        ('artist', artist),
        ('title', title),
        ('bucket', 'audio_summary'),
        ('bucket', 'song_hotttnesss'),
    ]
    fp = urllib2.urlopen("http://developer.echonest.com/api/v4/song/search?%s" % urllib.urlencode(params))
    data = fp.read()
    fp.close()
    return json.loads(data)


@app.route('/api/data')
def api_data():
    song = search_en()['response']['songs'][0]
    r = get_redis()
    key = 'cache:data:%s' % (song['id'])
    if not r.exists(key) and CACHING:
        analysis_url = song['audio_summary']['analysis_url']
        fp = urllib2.urlopen(analysis_url)
        data = json.loads(fp.read())
        fp.close()
        song['loudness'] = OrderedDict([(item['start'], item['loudness_max'])
             for item in data['segments']])
        if CACHING:
            r.set(key, json.dumps(song))
    else:
        song = json.loads(r.get(key))

    i = r.lindex('latest_staches', song['id'])

    if i != 0:
        r.lpush('latest_staches', song['id'])

    return jsonify({'song': song})
