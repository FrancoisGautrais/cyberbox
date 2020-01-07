from os import path

from src.http_server import log
from src.http_server.httpserver import HTTPServer

def SERVER_SINGLE_THREAD():
    return HTTPServer.SINGLE_THREAD

def SERVER_SPAWN_THREAD():
    return HTTPServer.SPAWN_THREAD

def SERVER_CONST_THREAD(n):
    return { "mode" : HTTPServer.CONST_THREAD, "n_threads" : n}


test = 23
WWW_DIR = "www"
LISTEN_HOST = ""
LISTEN_PORT = 8080
SHARE_DIR = "share/"
SAVE_DIR = "save/"
LOG_LEVEL = 0
PIDFILE="/var/run/cyberbox.pid"
SERVER=SERVER_CONST_THREAD(4)
USE_CACHE=False
USE_BROWSER_CACHE=False

class Conf:
    _INITIALIZED=False
    def __init__(self):
        pass

if not Conf._INITIALIZED:
    log.info("Reading config file '../conf/cyberbox.conf' ....")
    with open("../conf/cyberbox.conf") as f:
        exec(f.read())
    if SHARE_DIR[-1]!="/": SHARE_DIR+="/"
    if SAVE_DIR[-1]!="/": SAVE_DIR+="/"
    log.info("\tConfig OK")

SRC_ABS_PATH = path.dirname(path.abspath(__file__))
BASE_ABS_PATH = path.normpath(path.join(SRC_ABS_PATH, ".."))
SHARE_ABS_PATH = path.normpath(path.join(BASE_ABS_PATH, SHARE_DIR))
WWW_ABS_PATH = path.normpath(path.join(BASE_ABS_PATH, WWW_DIR))
WWW_SAVE_PATH = path.normpath(path.join(BASE_ABS_PATH, SAVE_DIR))

def www(x) : return path.normpath(path.join(WWW_ABS_PATH, x))
def share(x) : return path.normpath(path.join(SHARE_ABS_PATH, x))
def base(x) : return path.normpath(path.join(BASE_ABS_PATH, x))
def save(x) : return path.normpath(path.join(BASE_ABS_PATH, x))

Conf._INITIALIZED=True