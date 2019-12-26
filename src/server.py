import os

from src.httpserver import log
from src.user import User
from .httpserver.restserver import HTTPRequest, HTTPResponse, HTTPServer
from src import conf
from .filedb import FileDB
from src.httpserver.htmltemplate.htmlgen import html_gen
from src.usersdb import UserDB
class Server(HTTPServer):
    UPLOAD_URL="/upload/"
    SHARE_URL = "/share/"
    BROWSE_URL = "/browse/"
    FILE_URL = "/file/"
    DELETE_URL = "/delete/"
    def __init__(self):
        HTTPServer.__init__(self, conf.LISTEN_HOST)
        self.db=FileDB.load()
        self.users=UserDB.load()

    def find_client(self, req : HTTPRequest, res : HTTPResponse, isAction):
        client=None
        if "session" in req.cookies:
            client=self.users.find_user(req.cookies["session"])
        if not client:
            client = self.users.new_user(req.header("User-Agent"))
            res.header("Set-Cookie", "session="+client.id+"; Max-Age="+str(User.DUREE_SESSION)+"; Path=/")
        if isAction: client.inc_actions()
        return client

    def handlerequest(self, req : HTTPRequest, res : HTTPResponse):
        client=self.find_client(req, res, False)
        if req.method=="GET":
            if req.path in (Server.SHARE_URL[:-1], Server.SHARE_URL):
                return self.handle_download(req, res, client)
            elif req.path.startswith(Server.BROWSE_URL) or req.path in (Server.BROWSE_URL[:-1], "/"):
                return self.handle_browse(req,res, client)
            elif req.path == "/preferences.html":
                res.serve_file_gen(conf.www("preferences.html"), client.json())
                return
            elif req.path.startswith(Server.FILE_URL):
                return self.handle_file_info(req, res, client)
            elif req.path.startswith(Server.DELETE_URL):
                return self.handle_file_delete(req, res, client)
            else:
                self.handle_www(req, res, client)
                return

        if req.method=="POST":
            if req.path.startswith(Server.UPLOAD_URL[:-1]):
                return self.handle_upload(req, res, client)
            if req.path=="/user/modify":
                return self.users.modify(client.id, req.body_json())
            if req.path=="/user/delete":
                return self.users.delete(client.id)
            if req.path.startswith(Server.FILE_URL):
                return self.handle_file_modify(req, res, client)

        self.handle_404(req, res)

    def handle_file_modify(self, req : HTTPRequest, res : HTTPResponse, client ):
        data=req.body_json()
        self.db.modify(req.path[Server.FILE_URL:], data)

    def handle_file_info(self, req : HTTPRequest, res : HTTPResponse , client):
        res.content_type("application/json")
        res.end(self.db.file_info(req.path[Server.FILE_URL:]))

    def handle_file_delete(self, req : HTTPRequest, res : HTTPResponse, client ):
        self.db.remove(req.path[Server.FILE_URL:])

    def handle_www(self, req : HTTPRequest, res : HTTPResponse, client):
        #si le fichier n'existe pas
        path = conf.www(req.path[1:])
        if not os.path.isfile(path):
            return self.handle_404(req,res)
        res.serve_file(path)

    def handle_browse(self, req : HTTPRequest, res : HTTPResponse, client):
        relpath=req.path[len(Server.BROWSE_URL):]
        abspath = conf.share(relpath)
        if os.path.isdir(abspath):
            res.content_type("text/html")
            x=self.db.moustache(relpath, client.is_admin())
            res.end(html_gen(conf.www("browse.html"),{
                "path" : relpath,
                "ls" : x,
                "parent" : os.path.normpath(relpath+"/..") if (len(relpath)>0) else "",
                "is_root" :  (len(relpath)==0),
                "user" : client.json()
            }))
            return
        self.handle_404(req,res)

    def handle_download(self, req : HTTPRequest, res : HTTPResponse, client):
        relpath=req.path[len(Server.SHARE_URL):]
        abspath = conf.share(relpath)
        log.info("File downloaded '"+relpath+"'")

        #si le fichier n'existe pas
        if not os.path.isfile(abspath):
            return self.handle_404(req,res)

        res.serve_file(abspath, forceDownload=True)
        self.db.inc_download(relpath)

    def handle_upload(self, req : HTTPRequest, res : HTTPResponse, client):
        relapth=req.path[len(Server.UPLOAD_URL):]
        abspath=conf.SHARE_ABS_PATH
        if len(relapth): abspath+="/"+relapth
        x=req.multipart_next_file()
        log.info("File uploaded '"+relapth+"/"+x.filename+"'")
        while x:
            x.save(abspath)
            ret=self.db.add(relapth, x.filename)
            if not ret:
                res.code=403
                res.end("Accès interdit, fichier existant")
            x=req.multipart_next_file()

    def handle_404(self, req : HTTPRequest, res : HTTPResponse):
        res.code = 404
        res.msg = "Not Found"
        res.content_type("text/plain")
        res.end(req.path + " Not found")
