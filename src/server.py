import os

from src.httpserver import log
from src.user import User
from .httpserver.restserver import HTTPRequest, HTTPResponse, HTTPServer
from src import conf, error
from .filedb import FileDB
from src.httpserver.htmltemplate.htmlgen import html_gen
from src.usersdb import UserDB


CACHED_FILES=[ "/js/jquery.min.js", "/js/materialize.min.js", "/js/sha256.js", "/css/materialize.css" ]


def _size_compare(x, y): return (x["size"] if "size" in x else 0) - (y["size"] if "size" in y else 0)
def _date_compare(x, y): return x["creation"]-y["creation"]
def _name_compare(x, y): return x["name"].lower()-y["name"].lower()

def _size_key(x): return (x["size"] if "size" in x else 0)
def _date_key(x): return x["date"]
def _name_key(x): return x["name"].lower()

def _sort(array, _field, _order):
    algo=_size_key
    if _field=="date": algo=_date_key
    if _field=="name": algo=_name_key
    reverse=_order=="dec"
    return sorted(array, key=algo, reverse=reverse)


class Server(HTTPServer):
    NEW_DIR = "/createdir/"
    UPLOAD_URL="/upload/"
    SHARE_URL = "/share/"
    BROWSE_URL = "/browse/"
    FILE_URL = "/file/"
    DELETE_URL = "/delete/"
    LOGIN_URL = "/login/"
    DISCONNECT_URL = "/disconnect/"

    def __init__(self):
        HTTPServer.__init__(self, conf.LISTEN_HOST)
        self.db=FileDB.load()
        self.users=UserDB.load()

    def find_client(self, req : HTTPRequest, res : HTTPResponse, isAction):
        client=None
        if "session" in req.cookies:
            client=self.users.find_user(req.cookies["session"])
        if not client:
            client = self.users.new_user(req.header("User-Agent"), None)
            res.header("Set-Cookie", "session="+client.id+"; Max-Age="+str(User.DUREE_SESSION)+"; Path=/")
        if isAction: client.inc_actions()
        return client

    def handlerequest(self, req : HTTPRequest, res : HTTPResponse):
        client=self.find_client(req, res, False)
        if req.method=="GET":
            if req.path.startswith(Server.SHARE_URL) or  req.path==Server.SHARE_URL[:-1]:
                return self.handle_download(req, res, client)
            elif req.path.startswith(Server.BROWSE_URL) or req.path in (Server.BROWSE_URL[:-1], "/"):
                return self.handle_browse(req,res, client)
            elif req.path == "/preferences.html":
                res.serve_file_gen(conf.www("preferences.html"), { "user" : client.json() })
                return
            elif req.path.startswith(Server.FILE_URL):
                return self.handle_file_info(req, res, client)
            elif req.path.startswith(Server.DELETE_URL):
                return self.handle_file_delete(req, res, client)
            elif req.path==Server.LOGIN_URL or req.path==Server.LOGIN_URL[:-1]:
                return self.handle_login(req, res, client)
            elif req.path==Server.LOGIN_URL or req.path==Server.DISCONNECT_URL[:-1]:
                return self.handle_disconnect(req, res, client)
            else:
                self.handle_www(req, res, client)
                return

        if req.method=="POST":
            if req.path.startswith(Server.UPLOAD_URL[:-1]):
                return self.handle_upload(req, res, client)
            if req.path.startswith(Server.NEW_DIR[:-1]):
                return self.handle_new_dir(req, res, client)
            if req.path=="/user/modify":
                return self.users.modify(client.id, req.body_json())
            if req.path=="/user/delete":
                return self.users.delete(client.id)
            if req.path.startswith(Server.FILE_URL):
                return self.handle_file_modify(req, res, client)

        self.handle_404(req, res)

    def handle_file_modify(self, req : HTTPRequest, res : HTTPResponse, client ):
        data=req.body_json()
        parent=os.path.normpath(req.path[len(Server.FILE_URL):]+"/..")
        ret=self.db.modify(req.path[len(Server.FILE_URL):], data, client.is_admin())
        if ret==error.ERR_FORBIDDEN:
            res.code=403
            res.end("Écriture interdite sur '"+req.path[len(Server.FILE_URL):]+"'")
        elif ret==error.ERR_NOT_FOUND:
            res.code=404
            res.end("Dossier '"+parent+"'  non trouvé")


    def handle_file_info(self, req : HTTPRequest, res : HTTPResponse , client):
        file=self.db.find(req.path[len(Server.FILE_URL):])
        parent=os.path.normpath(req.path[len(Server.FILE_URL):-1]+"/..")
        if not file:
            res.code=404
            res.end("Fichier '"+req.path[len(Server.FILE_URL):]+"' non trouvé")
        elif not file.can_read(client.is_admin()):
            res.code=403
            res.end("Fichier '"+req.path[len(Server.FILE_URL):]+"' : accès non autorisé")
        else:
            res.content_type("application/json")
            res.end(file.json())

    def handle_file_delete(self, req : HTTPRequest, res : HTTPResponse, client ):
        ret=self.db.remove(req.path[len(Server.DELETE_URL):], client.is_admin())
        if ret==error.ERR_NOT_FOUND:
            res.code=404
            res.end("Fichier '"+req.path[len(Server.DELETE_URL):-1]+"' non trouvé")
        elif ret==error.ERR_FORBIDDEN:
            res.code=403
            res.end("Fichier '"+req.path[len(Server.DELETE_URL):-1]+"' : accès non autorisé")

    def handle_www(self, req : HTTPRequest, res : HTTPResponse, client):
        #si le fichier n'existe pas
        path = conf.www(req.path[1:])
        if not os.path.isfile(path):
            return self.handle_404(req,res)
        if req.path.startswith("/gen/") or len(req.path.split())==2:
            res.serve_file_gen(path, { "user" : client.json() })
        else:
            res.header("Last-Modified", "Wed, 21 Oct 2015 07:28:00 GMT")
            res.header("age", "30")
            if req.header("If-Modified-Since") and conf.USE_BROWSER_CACHE:
                res.code=304
                res.msg="Not Modified"
            else:
                res.serve_file(path)

    def handle_browse(self, req : HTTPRequest, res : HTTPResponse, client):
        relpath=req.path[len(Server.BROWSE_URL):]
        abspath = conf.share(relpath)
        if os.path.isdir(abspath):
            res.content_type("text/html")
            file=self.db.find(relpath)
            x=self.db.moustache(relpath, client.is_admin())
            x=_sort(x, client.sort, client.order)

            res.end(html_gen(conf.www("browse.html"),{
                "path" : relpath,
                "ls" : x,
                "parent" : os.path.normpath(relpath+"/..") if (len(relpath)>0) else "",
                "is_root" :  (len(relpath)==0),
                "user" : client.json(),
                "can_read" : file.can_read(client.is_admin()),
                "can_write" : file.can_write(client.is_admin())
            }))
            return
        else:
            self.handle_404(req,res)

    def handle_download(self, req : HTTPRequest, res : HTTPResponse, client):
        relpath=req.path[len(Server.SHARE_URL):]
        abspath = conf.share(relpath)
        log.info("File downloaded '"+relpath+"'")

        #si le fichier n'existe pas
        if not os.path.isfile(abspath):
            return self.handle_404(req,res)
        ret = self.db.find(relpath)
        if not ret:
            res.code=404
            res.content_type("text/plain")
            res.end("Fichier '"+relpath+"' non trouvé")
        elif not ret.can_read(client.is_admin()):
            res.code=403
            res.content_type("text/plain")
            res.end("Accès interdit sur '"+relpath+"'")
        else:
            res.serve_file(abspath, forceDownload=True)
            self.db.inc_download(relpath)

    def handle_upload(self, req : HTTPRequest, res : HTTPResponse, client):
        relapth=req.path[len(Server.UPLOAD_URL):]
        abspath=conf.SHARE_ABS_PATH
        if len(relapth): abspath+="/"+relapth
        x=req.multipart_next_file()
        dir=self.db.find(relapth)
        if not dir:
            res.code=404
            res.end("Dossier '"+relapth+"' non trouvé")
            return

        log.info("File uploaded '"+relapth+"/"+x.filename+"'")
        while x:
            if os.path.exists(os.path.join(abspath, x.filename)):
                res.code=403
                res.end("Le fichier "+os.path.join(relapth, x.filename)+" existe déja")

            x.save(abspath)
            ret=self.db.add(relapth, x.filename)
            if ret!=error.ERR_OK:
                if ret == error.ERR_FORBIDDEN:
                    res.code=403
                    res.end("Écriture interdite sur "+relapth)
            x=req.multipart_next_file()

    def handle_404(self, req : HTTPRequest, res : HTTPResponse):
        res.code = 404
        res.msg = "Not Found"
        res.content_type("text/plain")
        res.end(req.path + " Not found")

    def handle_new_dir(self, req : HTTPRequest, res : HTTPResponse, client):
        out=self.db.mkdir(req.path[len(Server.NEW_DIR):-1], client.is_admin(), {})
        parent=req.path[len(Server.NEW_DIR):req.path.rfind('/')]
        if out==error.ERR_FORBIDDEN:
            res.code=403
            res.content_type("text/plain")
            res.end("Écriture interdite sur '"+parent+"'")
        elif out==error.ERR_NOT_FOUND:
            res.code=404
            res.content_type("text/plain")
            res.end("Dossier '"+req.path[len(Server.NEW_DIR):-1]+"'  non trouvé")
        elif out==error.ERR_FILE_EXISTS:
            res.code=403
            res.content_type("text/plain")
            res.end("Le dossier '"+req.path[len(Server.NEW_DIR):-1]+"' existe déja")

    def handle_login(self, req : HTTPRequest, res : HTTPResponse, client):
        if client.name:
            res.code=301
            res.header("Location", "/")
        else:
            head=req.header("Authorization")
            if head  and "Basic " in head:
                user=self.users.authentification(head[7:])
                if user:
                    self.users.set_name(client.id, user)
                else:
                    res.code=401
                    res.content_type("text/plain")
                    res.end("Mauvais identifiant ou mot de passe")
            else:
                res.serve_file_gen(conf.www("login.html"), { "user" : client.json()})


    def handle_disconnect(self, req : HTTPRequest, res : HTTPResponse, client):
        self.users.set_name(client.id, None)
        res.code=301
        res.header("Location", "/")

        
