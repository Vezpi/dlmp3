import time

class Download(object):

    def __init__(self, song):
        self.song = song
        self.data = None
        self.chunksize = 16384
        self.bytesdone = 0
        self.t0 = time.time()

    def start(self, search):
        if not self.song.get_link():
            return False
        self.song.make_filename()
        self.data = session.search.urlopener(self.song.link)
        self.total = int(self.data.info()['Content-Length'].strip())
        self.outfh = open(self.song.filename, 'wb')
        return True

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
