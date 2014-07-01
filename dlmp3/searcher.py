import dlmp3
from dlmp3 import Config
from urllib2 import build_opener, HTTPError, URLError
from urllib import urlencode
import time
import socket
import json
import re
import os

opener = build_opener()
ua = "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"
opener.addheaders = [("User-Agent", ua)]
urlopen = opener.open

def tidy(raw, field):
    """ Tidy HTML entities, format songlength if field is duration.  """
    if field == "duration":
        raw = time.strftime('%M:%S', time.gmtime(int(raw)))
    else:
        for r in (("&#039;", "'"), ("&amp;#039;", "'"), ("&amp;amp;", "&"),
                 ("  ", " "), ("&amp;", "&"), ("&quot;", '"')):
            raw = raw.replace(r[0], r[1])
    return raw

def get_average_bitrate(song):
    """ Calculate average bitrate of VBR tracks. """
    if song["rate"] == "VBR":
        vbrsize = float(song["Rsize"][:-3]) * 8192
        vbrlen = float(song["Rduration"])
        vbrabr = int(vbrsize / vbrlen)
        if vbrabr > 320:
            vbrabr = 320
        song["listrate"] = str(vbrabr) + " v"  # for display in list
        song["rate"] = str(vbrabr) + " Kb/s VBR"  # for playback display
    else:
        song["listrate"] = song["rate"][:3]  # not vbr list display
    return song

def get_tracks_from_page(page):
    """ Get search results from web page. """
    fields = "duration file_id singer song link rate size source".split()
    matches = re.findall(r"\<li.(duration[^>]+)\>", page)
    songs = []
    if matches:
        for song in matches:
            cursong = {}
            for f in fields:
                v = re.search(r'%s=\"([^"]+)"' % f, song)
                if v:
                    cursong[f] = tidy(v.group(1), f)
                    cursong["R" + f] = v.group(1)
                else:
                    cursong[f] = "unknown"
                    cursong["R" + f] = "unknown"
                    #raise Exception("problem with field " + f)
            cursong = get_average_bitrate(cursong)
            songs.append(cursong)
    else:
        # dbg("got unexpected webpage or no search results")
        return False
    return songs

def get_top(period="w", page=1):
    period = period or "w"
    periods = "_ w 3m 6m year all".split()
    period = periods.index(period)
    """ Get top music for period, returns songs list."""
    url = ("http://pleer.com/en/gettopperiod?target1=%s&target2=r1&select=e&"
           "page_ru=1&page_en=%s")
    url = url % ("e%s" % period, page)
    try:
        wdata = urlopen(url).read().decode("utf8")
    except (URLError, HTTPError) as e:
        dlmp3.message = Color.red +  "no data" + Color.white
        return
    # dbg("fetched " + url)
    match = re.search(r"<ol id=\"search-results\">[\w\W]+?<\/ol>", wdata)
    html_ol = match.group(0)
    dlmp3.songlist = get_tracks_from_page(html_ol)
    songs = dlmp3.songlist
    return songs

def do_search(term, page=1):
    """ Perform search. """
    original_term = term
    url = "http://pleer.com/search"
    query = {"target": "tracks", "page": page}
    if not "+tous" in term:
        query["quality"] = "best"
    else:
        term = term.replace(" +tous", "")
    query["q"] = term
    query = [(k, query[k]) for k in sorted(query.keys())]
    url = "%s?%s" % (url, urlencode(query))
    try:
        wdata = urlopen(url).read().decode("utf8")
        songs = get_tracks_from_page(wdata)
    except (URLError, HTTPError) as e:
        dlmp3.message = Color.red +  "no data" + Color.white
        return
    if songs:
        dlmp3.songlist = songs
        dlmp3.last_opened = ""
        dlmp3.last_search_query = original_term
        dlmp3.current_page = page
        return songs
    else:
        dlmp3.current_page = 1
        dlmp3.last_search_query = ""
        return

def make_filename(song):
    """" Create download directory, generate filename. """
    if not os.path.exists(Config.DLDIR):
        os.makedirs(Config.DLDIR)
    filename = song['singer'][:49] + " - " + song['song'][:49] + ".mp3"
    filename = os.path.join(Config.DLDIR, filename)
    return filename

def get_stream(song, force=False):
    """ Return the url for a song. """
    if not "track_url" in song or force:
        url = 'http://pleer.com/site_api/files/get_url?action=download&id=%s'
        url = url % song['link']
        try:
            # dbg("[0] fetching " + url)
            wdata = urlopen(url, timeout=7).read().decode("utf8")
            # dbg("fetched " + url)
        except (HTTPError, socket.timeout):
            time.sleep(2)  # try again
            # dbg("[1] fetching 2nd attempt ")
            wdata = urlopen(url, timeout=7).read().decode("utf8")
            # dbg("fetched 2nd attempt" + url)
        j = json.loads(wdata)
        if not j.get("track_link"):
            raise URLError("This track is not accessible")
        track_url = j['track_link']
        return track_url
    else:
        return song['track_url']

