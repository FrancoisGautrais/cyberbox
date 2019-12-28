from src.httpserver.afdurl import AfdUrl

from src import conf
from src.server import Server
import sys
import os
import signal
from src.httpserver import log
from src.httpserver.filecache import filecache


def do_pidfile():
    if sys.platform.startswith("linux"):
        try:
            with open(conf.PIDFILE, "w") as f:
                f.write(str(os.getpid()))
        except:
            log.error("Impossible de creer le fichier pid ", conf.PIDFILE)
            pass
    else:
        log.info("Running on windows, no pidfile")

def get_server_pid():
    out=-1
    try:
        with open(conf.PIDFILE, "r") as f:
            return int(f.read())
    except:
        return -1

def start_server():
    filecache.init()
    do_pidfile()
    serv = Server()
    serv.listen(conf.LISTEN_PORT)

def print_help():
    print("Usage: ",sys.argv[0],"[OPTION] (start,stop)")
    print("\tOPTION:")
    print("\t\t-i | --ip HOST")
    print("\t\t-p | --p PORT")
    print("\t\t-h | --help : this help")

log.info(*sys.argv)
def start():
    i=1
    done=False
    while i<len(sys.argv):
        arg=sys.argv[i]
        if arg in [ "-i", "--ip"]:
            conf.LISTEN_HOST=sys.argv[i+1]
            i+=1
            done=True
        elif arg in ["-p", "--port"] :
            conf.LISTEN_PORT=int(sys.argv[i+1])
            i+=1
            done=True
        elif arg in ["stop"]:
            pid=get_server_pid()
            if pid>0: os.kill(pid, signal.SIGKILL)
            done=True
        elif arg in ["start"]:
            start_server()
            done=True
        elif arg in ["-h", "--help"]:
            print_help()
            done=True

        i+=1

    if not done:
        start_server()

start()