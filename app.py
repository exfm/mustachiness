from flask import Flask, render_template, jsonify, request, json, redirect
from exfm import ExfmClient
from werkzeug.routing import BaseConverter
from werkzeug.urls import url_fix
import urllib
import urllib2
from collections import OrderedDict
import redis

CACHING = True

app = Flask(__name__)
app.config.from_pyfile('settings_local.py')


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


def get_similar_song_ids(song_id):
    r = get_redis()

    key = 'cache:similar:%s' % (song_id)
    if not r.exists(key):
        params = [
            ('api_key', 'N6E4NIOVYMTHNDM8J'),
            ('song_id', song_id)
        ]
        _ = "http://developer.echonest.com/api/v4/playlist/basic?%s" % urllib.urlencode(params)
        fp = urllib2.urlopen(_)
        data = fp.read()
        fp.close()
        resp = json.loads(data)
        song_ids = [i['id'] for i in resp['response']['songs']]
        r.set(key, json.dumps(song_ids))
    else:
        song_ids = json.loads(r.get(key))
    return song_ids


def get_song(id=None):
    song = search_en(id=id)
    if not isinstance(song, dict):
        return song

    song = song['response']['songs'][0]
    r = get_redis()
    key = 'cache:data:%s' % (song['id'])
    if not r.exists(key):
        analysis_url = song['audio_summary']['analysis_url']
        try:
            fp = urllib2.urlopen(analysis_url)
            data = json.loads(fp.read())
            fp.close()
        except AttributeError, e:
            print e, analysis_url
            return {}

        song['loudness'] = OrderedDict([(item['start'], item['loudness_max'])
             for item in data['segments']])
        if CACHING:
            r.set(key, json.dumps(song))
        r.lpush('latest_staches', song['id'])

    else:
        song = json.loads(r.get(key))
    return song


@app.context_processor
def _context_processor():
    r = get_redis()
    num_staches = r.llen('latest_staches')
    return {'num_staches': num_staches}


@app.route('/')
def index():
    return render_template("index.html", songs=get_latest(0, 5))


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/song/<song_id>/buy/<what>')
def about():
    return render_template("about.html")


@app.route('/make')
def make():
    song = get_song()
    if not isinstance(song, dict):
        return song

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


@app.route('/song/<song_id>')
def song_page(song_id):
    song = get_song(song_id)
    songs = [get_song(_) for _ in get_similar_song_ids(song_id)]
    return render_template("similar.html", song=song,
        songs=songs)


@app.route('/years/<year_start>/<year_end>')
def get_song_years(year_start, year_end):
    song_ids = get_song_ids_for_years(year_start, year_end)
    songs = [get_song(_) for _ in song_ids]
    return render_template("years.html", songs=songs,
        year_start=year_start, year_end=year_end)


def get_lastfm_image(name):
    params = [
        ('api_key', 'b25b959554ed76058ac220b7b2e0a026'),
        ('method', 'artist.getimages'),
        ('artist', name),
        ('limit', 1),
        ('format', 'json')

    ]
    url = "http://ws.audioscrobbler.com/2.0/?%s" % urllib.urlencode(params)
    fp = urllib2.urlopen(url)
    data = fp.read()
    fp.close()
    data = json.loads(data)
    try:
        return data['images']['image']['sizes']['size'][-1]['#text']
    except:
        return None


@app.route('/artist/<name>')
def get_artist(name):
    song_ids = get_artist_song_ids(name)
    songs = [get_song(_) for _ in song_ids]

    artist_image = get_lastfm_image(name)

    return render_template("artist.html", songs=songs,
        name=name, artist_image=artist_image)


def get_artist_song_ids(name):
    params = [
        ('api_key', 'N6E4NIOVYMTHNDM8J'),
        ('name', name)
    ]

    _ = "http://developer.echonest.com/api/v4/artist/songs?%s" % (urllib.urlencode(params))
    print _
    fp = urllib2.urlopen(_)
    data = fp.read()
    fp.close()
    data = json.loads(data)
    song_ids = [song['id'] for song in data['response']['songs']]
    return song_ids


@app.route('/genre/<genre>')
def get_genre(genre):
    songs = get_songs_in_genre(genre)
    return render_template("genre.html", songs=songs,
        genre=genre)


def get_songs_in_genre(genre):
    params = [
        ('api_key', 'N6E4NIOVYMTHNDM8J'),
        ('bucket', 'audio_summary'),
        ('bucket', 'song_hotttnesss'),
        ('style', genre),
        ('sort', 'song_hotttnesss-desc')
    ]

    method = "search"

    _ = "http://developer.echonest.com/api/v4/song/%s?%s" % (method, urllib.urlencode(params))
    print _
    fp = urllib2.urlopen(_)
    data = fp.read()
    fp.close()
    data = json.loads(data)
    r = get_redis()
    songs = []
    for song in data['response']['songs']:
        key = 'cache:data:%s' % (song['id'])
        if not r.exists(key):
            analysis_url = song['audio_summary']['analysis_url']
            try:
                fp = urllib2.urlopen(analysis_url)
                data = json.loads(fp.read())
                fp.close()
            except AttributeError, e:
                print e, analysis_url
                return {}

            song['loudness'] = OrderedDict([(item['start'], item['loudness_max'])
                 for item in data['segments']])
            if CACHING:
                r.set(key, json.dumps(song))
            r.lpush('latest_staches', song['id'])

        else:
            song = json.loads(r.get(key))
        songs.append(song)

    return songs


def get_song_ids_for_years(year_start, year_end):
    r = get_redis()
    key = "cache:years:%s:%s" % (year_start, year_end)
    if r.exists(key):
        return json.loads(r.get(key))

    params = [
        ('api_key', 'N6E4NIOVYMTHNDM8J'),
        ('bucket', 'songs'),
        ('artist_start_year_before', year_start),
        ('artist_end_year_after', year_end),
        ('sort', 'familiarity-desc')
    ]
    _ = "http://developer.echonest.com/api/v4/artist/search?%s" % urllib.urlencode(params)
    print _
    fp = urllib2.urlopen(_)
    data = fp.read()
    fp.close()
    resp = json.loads(data)

    song_ids = []
    for artist in resp['response']['artists']:
        if artist['songs']:
            song_ids.extend(map(lambda x: x['id'], artist['songs'][0:1]))
    r.set(key, json.dumps(song_ids))
    return song_ids


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

    artist = artist.strip()
    title = title.strip()
    if not title:
        return redirect('/artist/%s' % artist)

    return artist, title


def search_en(id=None):
    params = [
        ('api_key', 'N6E4NIOVYMTHNDM8J'),
        ('bucket', 'audio_summary'),
        ('bucket', 'song_hotttnesss'),
    ]
    artist = None
    title = None

    if id or request.values.get('id'):
        _ = request.values.get('id', id)
        params.extend([('id', _)])

    elif request.values.get('q'):

        res = extract(request.values.get('q'))
        if not isinstance(res, tuple):
            return res

        artist, title = res
    else:
        artist = request.values.get('artist')
        title = request.values.get('title')

    if artist and title:
        params.extend([('artist', artist), ('title', title)])

    if id or request.values.get('id'):
        method = "profile"
    else:
        method = "search"

    _ = "http://developer.echonest.com/api/v4/song/%s?%s" % (method, urllib.urlencode(params))

    fp = urllib2.urlopen(_)
    data = fp.read()
    fp.close()
    return json.loads(data)


@app.route('/api/data')
def api_data():
    return jsonify({'song': get_song()})

@app.route('/api/artist/<name>/image')
def api_artist_image():
    return jsonify({'song': get_song()})


@app.route('/upload-stache', methods=['POST'])
def upload_stache():
    import base64
    import tempfile
    import boto
    from boto.s3.key import Key
    import re

    dataUrlPattern = re.compile('data:image/(png|jpeg);base64,(.*)$')

    conn = boto.connect_s3(app.config['AWS_KEY'], app.config['AWS_SECRET'])

    song_id = request.values.get('song_id')
    imgb64 = dataUrlPattern.match(request.values.get('stache')).group(2)
    data = base64.b64decode(imgb64)

    fp = tempfile.NamedTemporaryFile()
    # fp = open(song_id, 'w')
    fp.write(data)

    bucket = conn.get_bucket('staches')
    headers = {'Content-Type': 'image/png'}

    k = Key(bucket)
    k.key = "%s.png" % (song_id)
    k.set_contents_from_file(fp, headers=headers)
    k.set_acl('public-read')
    fp.close()

    r = get_redis()
    key = 'cache:data:%s' % (song_id)
    song = json.loads(r.get(key))
    song['s3_url'] = "http://staches.s3.amazonaws.com/%s" % k.key
    song['stache_version'] = '0.1'
    r.set(key, json.dumps(song))
    return song['s3_url']
