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


def get_latest(start, results):
    r = get_redis()
    ids = r.lrange('latest_staches', start, results)
    pipe = r.pipeline()
    [pipe.get('cache:data:%s' % _) for _ in ids]
    res = pipe.execute()
    songs = [json.loads(x) for x in res]
    return songs


def get_song():
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
        r.lpush('latest_staches', song['id'])

    else:
        song = json.loads(r.get(key))
    return song


@app.route('/')
def index():
    return render_template("index.html", songs=get_latest(0, 5))


@app.route('/make')
def make():
    song = get_song()
    return render_template("make.html", song=song)


@app.route('/latest')
def latest():
    r = get_redis()
    total = r.llen('latest_staches')
    start = request.values.get('start', 0)
    results = request.values.get('results', 10)

    has_more = total < (start + total)
    has_less = start > 0

    return render_template("latest.html",
        songs=get_latest(start, results), has_more=has_more, has_less=has_less)


@app.route('/api/latest')
def api_latest():
    songs = get_latest(request.values.get('start', 0), request.values.get('results', 20))
    return jsonify({'staches': songs})


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
    params = [
        ('api_key', 'N6E4NIOVYMTHNDM8J'),
        ('bucket', 'audio_summary'),
        ('bucket', 'song_hotttnesss'),
    ]
    artist = None
    title = None

    if request.values.get('id'):
        params.extend([('id', request.values.get('id'))])
    elif request.values.get('q'):
        artist, title = extract(request.values.get('q'))
    else:
        artist = request.values.get('artist')
        title = request.values.get('title')

    if artist and title:
        params.extend([('artist', artist), ('title', title)])

    fp = urllib2.urlopen("http://developer.echonest.com/api/v4/song/search?%s" % urllib.urlencode(params))
    data = fp.read()
    fp.close()
    return json.loads(data)


@app.route('/api/data')
def api_data():
    return jsonify({'song': get_song()})
