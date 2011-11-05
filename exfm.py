try:
    import simplejson as json
except ImportError:
    import json

import urllib
import urllib2
import hashlib


class ExfmError(Exception):
    pass


class ExfmClient(object):

    def __init__(self):
        pass

    def _post(self, route, data={}):
        return self._make_request(route, data, method='POST')

    def _get(self, route, data={}):
        return self._make_request(route, data, method='GET')

    def _make_request(self, route, data, method='GET'):
        url = "http://ex.fm/api/v3%s" % route

        data = urllib.urlencode(data, True)
        headers = {'User-Agent': 'exfm API Python Client'}

        try:
            if method == 'POST':
                req = urllib2.Request(url, data=data, headers=headers)
            else:
                url += '?' + data
                req = urllib2.Request(url, headers=headers)

            response_data = urllib2.urlopen(req).read()
            data = json.loads(response_data)

            if data['status_code'] != 200:
                raise ExfmError(data['status_text'])

            return data
        except urllib2.HTTPError, e:
            return e.read()
        except urllib2.URLError, e:
            return str(e)

    def hash(self, password):
        return hashlib.md5(password).hexdigest()

    def get_user(self, username):
        return self._get("/user/%s" % username)

    def get_user_loved(self, username, start=0, results=20):
        return self._get("/user/%s/loved" % username)

    def get_user_followers(self, username, start=0, results=20):
        return self._get("/user/%s/followers" % username,
            data={'start': start, 'results': results})

    def get_user_following(self, username, start=0, results=20):
        return self._get("/user/%s/following" % username,
            data={'start': start, 'results': results})

    def get_user_following_ids(self, username):
        return self._get("/user/%s/following_ids" % username)

    def get_user_feed_love(self, username, start=0, results=20):
        return self._get("/user/%s/feed/love" % username,
            data={'start': start, 'results': results})

    def get_user_activity(self, username, start=0, results=20):
        return self._get("/user/%s/activity" % username,
            data={'start': start, 'results': results})

    def get_user_activity_with_verb(self, username, verb='love', start=0, results=20):
        return self._get("/user/%s/activity/%s" % (username, verb),
            data={'start': start, 'results': results})

    def get_user_notifications(self, username, start=0, results=20):
        return self._get("/user/%s/notifications" % username,
            data={'start': start, 'results': results})

    def get_song(self, song_id):
        return self._get("/song/%s" % song_id)

    def get_song_search_results(self, query):
        return self._get("/song/search/%s" % query)

    def get_song_graph(self, song_id):
        return self._get("/song/%s/graph" % song_id)

    def love_song(self, username, password, song_id, client_id='exfm_api',
        context=None, source=None):
        password_hash = self.hash(password)
        data = {
            'username': username,
            'password': password_hash,
            'client_id': client_id,
            'context': context,
            'source': source
        }

        return self._post("/song/%s/love" % song_id, data)

    def unlove_song(self, username, password, song_id):
        password_hash = self.hash(password)
        data = {
            'username': username,
            'password': password_hash
        }
        return self._post("/song/%s/unlove" % song_id, data)

    def get_loved_on_url(self, url):
        return self._get("/url/%s/loved" % url)

    def get_trending(self, start=0, results=20):
        return self._get("/trending", data={'start': start, 'results': results})

    def get_sotd(self):
        return self._get("/sotd")

    def get_motm(self):
        return self._get("/motm")

    def get_aotw(self):
        return self._get("/aotw")

    def get_explore(self, genre=None, start=0, results=20):
        route = "/explore"
        if genre:
            route += "/%s" % genre
        return self._get(route, data={'start': start, 'results': results})