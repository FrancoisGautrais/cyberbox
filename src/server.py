import os



from src.http_server import log, utils
from src.user import User
from .http_server.restserver import HTTPRequest, HTTPResponse, HTTPServer
from src import conf, error
from .filedb import FileDB
from src.http_server.htmltemplate.htmlgen import html_gen
from src.usersdb import UserDB
from src.http_server.restserver import RESTServer

CACHED_FILES=[ "/js/jquery.min.js", "/js/materialize.min.js", "/js/sha256.js", "/css/materialize.css" ]


def _size_compare(x, y): return (x["size"] if "size" in x else 0) - (y["size"] if "size" in y else 0)
def _date_compare(x, y): return x["creation"]-y["creation"]
def _name_compare(x, y): return x["name"].lower()-y["name"].lower()

def _size_key(x): return (x["size"] if "size" in x else 0)
def _date_key(x): return x["creation"]
def _name_key(x): return x["name"].lower()

def _sort(array, _field, _order):
    algo=_size_key
    if _field=="date": algo=_date_key
    if _field=="name": algo=_name_key
    reverse=_order=="dec"
    return sorted(array, key=algo, reverse=reverse)


class Server(RESTServer):
    NEW_DIR_URL = "/createdir/"
    UPLOAD_URL="/upload/"
    SHARE_URL = "/share/"
    BROWSE_URL = "/browse/"
    FILE_URL = "/file/"
    DELETE_URL = "/delete/"
    LOGIN_URL = "/login/"
    SEARCH_URL = "/search/"
    RESULTS_URL = "/results/"
    DISCONNECT_URL = "/disconnect/"

    def __init__(self):
        RESTServer.__init__(self, conf.LISTEN_HOST, conf.SERVER)
        self.db=FileDB.load()
        self.users=UserDB.load()
        self.route("GET", "/", self.handle_redirect)
        self.route("GET", Server.SHARE_URL+"*path", self.handle_download)
        self.route("GET", Server.BROWSE_URL+"*path", self.handle_browse)
        self.route("GET", ["/preferences.html", "/preferences"], self.handle_preferences)
        self.route("GET", Server.FILE_URL+"*path", self.handle_file_info)
        self.route("GET", Server.DELETE_URL+"*path", self.handle_file_delete)
        self.route("GET", Server.LOGIN_URL, self.handle_login)
        self.route("GET", Server.SEARCH_URL, self.handle_search)
        self.route("GET", Server.DISCONNECT_URL, self.handle_disconnect)
        self.route("GET", Server.NEW_DIR_URL+"*path", self.handle_new_dir)
        self.route("GET", "/session/delete", self.handle_session_delete)
        self.default(self.handle_www, methods="GET")

        self.route("POST", Server.UPLOAD_URL+"*path", self.handle_upload)
        self.route("POST", Server.FILE_URL+"*path", self.handle_file_modify)
        self.route("POST", "/user/modify", self.handle_client_modify)
        self.route("POST", "/user/delete", self.handle_client_delete)
        self.route("POST", Server.RESULTS_URL, self.handle_results)
        self.default(self.handle_404, methods="POST")

    def find_client(self, req : HTTPRequest, res : HTTPResponse, isAction):
        client=None
        if "session" in req.cookies:
            client=self.users.find_user(req.cookies["session"])
        if not client:
            client = self.users.new_user(req.header("User-Agent"), None)
            print(req._headers)
            res.header("Set-Cookie", "session="+client.id+"; Max-Age="+str(User.DUREE_SESSION)+"; Path=/")
        if isAction: client.inc_actions()
        return client

    def handle_client_modify(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        self.users.modify(client.id, req.body_json())

    def handle_client_delete(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        self.users.delete(client.id)

    def handle_preferences(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        res.serve_file_gen(conf.www("preferences.html"), {"user": client.json()})

    def handle_file_modify(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        path=req.params.str("path")
        data=req.body_json()
        parent=os.path.normpath(path+"/..")
        ret=self.db.modify(path, data, client.is_admin())
        if ret==error.ERR_FORBIDDEN:
            res.code=403
            res.end("Écriture interdite sur '"+path+"'")
        elif ret==error.ERR_NOT_FOUND:
            res.code=404
            res.end("Dossier '"+parent+"'  non trouvé")


    def handle_file_info(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        path=req.params.str("path")
        file=self.db.find(path)
        parent=os.path.normpath(path+"/..")
        if not file:
            res.code=404
            res.end("Fichier '"+path+"' non trouvé")
        elif not file.can_read(client.is_admin()):
            res.code=403
            res.end("Fichier '"+path+"' : accès non autorisé")
        else:
            res.content_type("application/json")
            res.end(file.info(client.is_admin()))

    def handle_file_delete(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        path=req.params.str("path")
        ret=self.db.remove(path, client.is_admin())
        if ret==error.ERR_NOT_FOUND:
            res.code=404
            res.end("Fichier '"+path+"' non trouvé")
        elif ret==error.ERR_FORBIDDEN:
            res.code=403
            res.end("Fichier '"+path+"' : accès non autorisé")

    def handle_www(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        #si le fichier n'existe pas
        path = conf.www(req.path[1:])
        lpath=utils.path_to_list(req.path[1:])
        if not os.path.isfile(path):
            return self.handle_404(req,res)

        #
        # Use Meta HTML with /*.html or /gen/**
        #
        if lpath and (lpath[0]=="gen" or (len(lpath)==1 and lpath[0].endswith(".html"))):
            res.serve_file_gen(path, { "user" : client.json() })
        else:
            res.header("Last-Modified", "Wed, 21 Oct 2015 07:28:00 GMT")
            res.header("age", "30")
            if req.header("If-Modified-Since") and conf.USE_BROWSER_CACHE: res.serve304()
            else: res.serve_file(path)

    def handle_browse(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        relpath=req.params.str("path")
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

    def handle_download(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        relpath=req.params.str("path")
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

    def handle_upload(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        relapth=req.params.str("path")
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

    def handle_new_dir(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        path=req.params.str("path")
        out=self.db.mkdir(path, client.is_admin(), {})
        parent=os.path.dirname(path)
        if out==error.ERR_FORBIDDEN:
            res.code=403
            res.content_type("text/plain")
            res.end("Écriture interdite sur '"+parent+"'")
        elif out==error.ERR_NOT_FOUND:
            res.code=404
            res.content_type("text/plain")
            res.end("Dossier '"+path+"'  non trouvé")
        elif out==error.ERR_FILE_EXISTS:
            res.code=403
            res.content_type("text/plain")
            res.end("Le dossier '"+path+"' existe déja")

    def handle_login(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
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


    def handle_disconnect(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        self.users.set_name(client.id, None)
        res.code=301
        res.header("Location", "/")

    def handle_search(self, req: HTTPRequest, res: HTTPResponse):
        client = self.find_client(req, res, False)
        res.serve_file_gen(conf.www("search.html"), {"user" : client.json()})

    def handle_results(self, req : HTTPRequest, res : HTTPResponse):
        client = self.find_client(req, res, False)
        search=req.body_json()
        l=self.db.search(search, client.is_admin())
        res.serve_file_gen(conf.www("browse.html"), {
            "path": "",
            "ls": l,
            "parent": "",
            "is_root": True,
            "user": client.json(),
            "can_read": True,
            "can_write": False
        })

    def handle_redirect(self, req : HTTPRequest, res : HTTPResponse):
        res.serve301("/browse")

    def handle_session_delete(self, req : HTTPRequest, res : HTTPResponse):
        res.header("Set-Cookie", "session=deleted; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT")