from os import path


test = 23
WWW_DIR = "www"
LISTEN_HOST = "localhost"
LISTEN_PORT = 8080
SHARE_URL = "/share/"
SHARE_DIR = "share/"

class Conf:
    _INITIALIZED=False
    def __init__(self):
        pass

if not Conf._INITIALIZED:
    with open("../conf/cyberbox.conf") as f:
        exec(f.read())
    if SHARE_URL[-1]!="/": SHARE_URL+="/"
    if SHARE_DIR[-1]!="/": SHARE_DIR+="/"

SRC_ABS_PATH = path.dirname(path.abspath(__file__))
BASE_ABS_PATH = path.normpath(path.join(SRC_ABS_PATH, ".."))
SHARE_ABS_PATH = path.normpath(path.join(BASE_ABS_PATH, SHARE_DIR))
WWW_ABS_PATH = path.normpath(path.join(BASE_ABS_PATH, WWW_DIR))

def www(x) : return path.normpath(path.join(WWW_ABS_PATH, x))
def share(x) : return path.normpath(path.join(SHARE_ABS_PATH, x))
def base(x) : return path.normpath(path.join(BASE_ABS_PATH, x))

Conf._INITIALIZED=True