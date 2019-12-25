from src import conf
from src.server import Server
import sys
import os
import signal



print(sys.argv)

def do_pidfile():
    if sys.platform.startswith("linux"):
        try:
            with open(conf.PIDFILE, "w") as f:
                f.write(str(os.getpid()))
        except:
            print("Impossible de creer le fichier pid ",conf.PIDFILE)
            pass
    else:
        print("Running on windows, no pidfile")

def get_server_pid():
    out=-1

    with open(conf.PIDFILE, "r") as f:
        return int(f.read())

def start_server():
    do_pidfile()
    serv = Server()
    serv.listen(conf.LISTEN_PORT)

def print_help():
    print("Usage: ",sys.argv[0],"[OPTION] (start,stop)")
    print("\tOPTION:")
    print("\t\t-i | --ip HOST")
    print("\t\t-p | --p PORT")
    print("\t\t-h | --help : this help")

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
            os.kill(get_server_pid(), signal.SIGKILL)
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