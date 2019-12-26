
import pystache
from threading import Lock
from threading import Thread
import hashlib




class Callback:

    def __init__(self, fct=None, obj=None, data=None):
        self.fct=fct
        self.obj=obj
        self.data=data


    def call(self, prependParams=(), appendParams=()):
        data=None
        if not self.fct: return None
        if self.data:
            data=prependParams+(self.data,)+appendParams

        if self.obj:
            if data:
                return self.fct(self.obj, *data)
            else:
                x=prependParams+appendParams
                if x:
                    return self.fct(self.obj, *x)
                else:
                    return self.fct(self.obj)
        else:
            if data:
                return self.fct(*data)
            else:
                x=prependParams+appendParams
                if x:
                    return self.fct(*x)
                else:
                    return self.fct()


class ThreadWrapper(Thread):

    def __init__(self, cb : Callback):
        Thread.__init__(self)
        self.cb=cb

    def run(self):
        self.cb.call()


def start_thread(cb : Callback):
    t=ThreadWrapper(cb)
    t.start()
    return t


def html_template(path, data):
    with filecache.open(path) as file:
        return pystache.render(file.read(), data)

def html_template_string(source, data):
    return pystache.render(source, data)

def sha256(s):
    m=hashlib.sha256()
    m.update(bytes(s, "utf-8"))
    return m.digest()
