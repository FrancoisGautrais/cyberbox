import os
import time
from io import StringIO
from io import BytesIO
import magic

from src.httpserver import log
from src.httpserver import utils


from threading import Lock
_mime_lock=None

if not _mime_lock:
    _mime_lock=Lock()

def _mime(path):
    try:
        _mime_lock.acquire()
        x=magic.detect_from_filename(path)
        mi= x.mime_type
        _mime_lock.release()
        return mi
    except:
        _mime_lock.release()
        return "text/plain"


FILETYPES=[".html", ".css", ".js", ".ttf", ".woff2"]
MAX_FILE_SIZE=1024*1024 # 1 Mio
class CacheEntry:

    def __init__(self, path : str):
        self.path=path
        self.time=time.time()
        self.cached=False
        self.data=None
        self.data_str=None
        self._update()


    def _update(self):
        self.mime=_mime(self.path)
        self.size=os.stat(self.path).st_size
        if self.size<=MAX_FILE_SIZE:
            for x in FILETYPES:
                if self.path.endswith(x):
                    self.cached=True
                    break
        if self.cached :
            with open(self.path, "rb") as f:
                self.data=f.read()
            self.data_str=self.data.decode("utf-8", "replace")

    def open(self, mode):
        if self.cached:
            if mode=="r":
                return StringIO(self.data_str)
            else:
                return BytesIO(self.data)
        else:
            log.debug("Cache fail for '"+self.path+"'")
            return open(self.path, mode)

    def _need_invalidate(self):
        return False

    def invalidate(self):
        return self._update()

    def get(self, invalid=False):
        if self._need_invalidate() or invalid:
            self.invalidate()
        return self


class FileCache:
    _INSTANCE=None
    def __init__(self, dirs=[]):
        self.db={}
        self.preload(dirs)
        self.bypass=False


    def find_total_size(self):
        acc=0
        for x in self.db:
            obj=self.db[x]
            acc+=obj.size*2
        return acc

    def _get_cached(self, path, invalidate):
        #le fichier n'est pas dans la cache
        if not path in self.db:
            x=CacheEntry(path)
            self.db[path]=x
            return x
        return self.db[path].get(invalidate)

    def preload(self, path):
        if isinstance(path, str): path=[path]
        for p in path:
            if os.path.isdir(p):
                tmp=[]
                for name in os.listdir(p):
                    tmp.append(os.path.join(p, name))
                self.preload(tmp)
            elif os.path.isfile(p):
                self._get_cached(p)

    def invalidate(self, path):
        return self._get_cached(path, True)

    def mime(self, path, invalidate=False):
        return self._get_cached(path, invalidate).mime if not self.bypass else utils.mime(path)

    def open(self, path, mode="r", invalidate=False):
        log.info("Total cache %.3f Mio"%(self.find_total_size()/1024/1024))
        return self._get_cached(path, invalidate).open(mode) if not self.bypass else open(path, mode)

class filecache:
    @staticmethod
    def init(dirs=[]): FileCache._INSTANCE=FileCache(dirs)

    @staticmethod
    def preload(path): return FileCache._INSTANCE.preload(path)

    @staticmethod
    def invalidate(path): return FileCache._INSTANCE.invalidate(path)

    @staticmethod
    def mime(path, inv=False): return FileCache._INSTANCE.mime(path, inv)

    @staticmethod
    def open(path, mode="r", inv=False): return FileCache._INSTANCE.open(path, mode, inv)
