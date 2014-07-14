from dlmp3 import session
from song import Songlist
from urllib2 import build_opener, HTTPError, URLError
from urllib import urlencode
from HTMLParser import HTMLParser
import socket
import json
import re
import time


class Search(object):
    """ Elements from a web search. """

    def __init__(self, nature, config, term=False):
        self.term = term
        self.web_data = ""
        self.nature = nature
        self.source = config.SOURCE
        self.page = 1
        self.last_search_query = ""
        self.opener = build_opener()
        self.ua = "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"
        self.opener.addheaders = [("User-Agent", self.ua)]
        self.urlopener = self.opener.open

    def deezer(self):
        """ Get charts from Deezer. """
        deezer_id = 0
        url = "http://api.deezer.com/editorial/%s/charts"
        url = url % deezer_id 
        wdata = json.loads(self.urlopener(url).read()) # dict (unicode)
        return (wdata["tracks"]["data"], "deezer")


    def pleer(self):
        """ Perform search or get charts from pleer.com. """
        if self.nature == "search":
            return (self.pleer_search(), "pleer")
        if self.nature == "charts":
            return (self.pleer_charts(), "pleer")

    def pleer_charts(self):
        """ Get charts from pleer.com. """
        period = self.period or "w"
        periods = "_ w 3m 6m year all".split()
        period = periods.index(period)
        """ Get top music for period, returns songs list."""
        url = ("http://pleer.com/en/gettopperiod?target1=%s&target2=r1&select=e&"
               "page_ru=1&page_en=%s")
        url = url % ("e%s" % period, self.page)
        try:
            wdata = self.urlopener(url).read().decode("utf8")
        except (URLError, HTTPError) as e:
            return
        match = re.search(r"<ol id=\"search-results\">[\w\W]+?<\/ol>", wdata)
        html_ol = match.group(0)
        return self.get_tracks_from_page(html_ol) 

    def pleer_search(self):
        """ Perform search from pleer.com. """
        original_term = self.term
        url = "http://pleer.com/search"
        query = {"target": "tracks", "page": self.page}
        if not "+tous" in self.term:
            query["quality"] = "best"
        else:
            self.term = self.term.replace(" +tous", "")
        query["q"] = self.term
        query = [(k, query[k]) for k in sorted(query.keys())]
        url = "%s?%s" % (url, urlencode(query))
        try:
            wdata = self.urlopener(url).read().decode("utf8")
            songs = self.get_tracks_from_page(wdata)
        except (URLError, HTTPError) as e:
            return
        if songs:
            return songs
        else:
            return

    def get_link(self, song):
        url = 'http://pleer.com/site_api/files/get_url?action=download&id=%s'
        url = url % song.id
        try:
            wdata = self.urlopener(url, timeout=7).read().decode("utf8")
        except (HTTPError, socket.timeout):
            time.sleep(2)  # try again
            wdata = self.urlopener(url, timeout=7).read().decode("utf8")
        return json.loads(wdata)

    def tidy(self, raw):
        """ Tidy HTML entities. """
        for r in (("&#039;", "'"), ("&amp;#039;", "'"), ("&amp;amp;", "&"),
                 ("  ", " "), ("&amp;", "&"), ("&quot;", '"')):
            raw = raw.replace(r[0], r[1])
        return raw

    def get_average_bitrate(self, song):
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

    def get_tracks_from_page(self, page):
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
                        cursong[f] = self.tidy(v.group(1))
                        cursong["R" + f] = v.group(1)
                    else:
                        cursong[f] = "unknown"
                        cursong["R" + f] = "unknown"
                cursong = self.get_average_bitrate(cursong)
                songs.append(cursong)
        else:
            return False
        return songs

    def mp3download(self):
        """ Perform search from mp3download.pw. """
        url = "http://mp3download.pw/mp3/"
        url = url + self.term.replace(" ", "-")
        wdata = self.urlopener(url).read()
        parser = Mp3DownloadParser()
        parser.feed(wdata)
        return (parser.songlist, "mp3download")

    def next(self):
        """ Get next search results. """
        self.page += 1
        if self.do():
            return True
        else:
            self.page -= 1
            return False

    def prev(self):
        """ Get previous search results. """
        if self.page > 1:
            self.page -= 1
        if self.do():
            return True
        else:
            self.page += 1
            return False

    def do(self):
        """ Launch the search. """
        if self.nature == "search":
            if self.source == "pleer":
                songlist = Songlist(self.pleer())
            elif self.source == "mp3download":
                songlist = Songlist(self.mp3download())
        elif self.nature == "charts":
            if self.source == "deezer":
                songlist = Songlist(self.deezer())
            else:
                songlist = Songlist(self.pleer())
        if songlist.songs:
            session.songlist = songlist
            return True
        else:
            return False   


class Download(object):

    def __init__(self, song):
        self.song = song
        self.data = None
        self.chunksize = 16384
        self.bytesdone = 0
        self.t0 = time.time()

    def start(self, config, search):
        try:
            if not self.song.get_link(search):
                return False
            self.song.make_filename(config)
            self.data = search.urlopener(self.song.link)
            self.total = int(self.data.info()['Content-Length'].strip())
            self.outfh = open(self.song.filename, 'wb')
            return True
        except HTTPError:
            return False

    def get(self):
        chunk = self.data.read(self.chunksize)
        self.outfh.write(chunk)
        elapsed = time.time() - self.t0
        self.bytesdone += len(chunk)
        self.rate = (self.bytesdone / 1024) / elapsed
        self.eta = (self.total - self.bytesdone) / (self.rate * 1024)
        if not chunk:
            self.outfh.close()
            return False
        return True


class Mp3DownloadParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_list = False
        self.print_data = False
        self.in_track = False
        self.title = False
        self.track = []
        self.songlist = []
        self.list_count = 0
        self.last_count = 0
    def handle_starttag(self, tag, attr):
        if tag == "li":
            self.in_list = True
            self.list_count += 1
        if tag == "h4":
            self.print_data = True
            self.in_track = True
            self.title = True
            self.track = []
        if self.in_track:
            if tag == "a":
                for tuples in attr:
                    if tuples[0] == "href":
                        self.track.append(tuples[1])
            if tag == "div":
                self.print_data = True
                self.songlist.append(self.track)                
    def handle_data(self, data):
        if self.print_data:
            if self.title:
                data = data.replace('.mp3 download', '')
                if not self.last_count == self.list_count:
                    self.last_count += 1
                    self.track.append(data)
                else:
                    self.track[-1] = self.track[-1] + data
            else:
                data = data.replace('\n', '').replace(' ', '')
                self.track.append(data)
    def handle_endtag(self, tag):
        if tag == "h4":
            self.print_data = False
            self.title = False
        if self.in_track:
            if tag == "div":
                self.print_data = False
            if tag == "li":
                self.in_track = False
                self.in_list = False

