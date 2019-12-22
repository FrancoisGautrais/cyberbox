import os
from .httpserver.restserver import Callback, HTTPRequest, HTTPResponse, HTTPServer
from src import conf
from os import path
import pystache
from .filedb import FileDB

def html_template(path, data):
    with open(path) as file:
        return pystache.render(file.read(), data)

class Server(HTTPServer):
    UPLOAD_URL="/upload/"
    SHARE_URL = "/share/"
    BROWSE_URL = "/browse/"
    def __init__(self):
        HTTPServer.__init__(self, conf.LISTEN_HOST)
        self.db=FileDB.load()

    def handlerequest(self, req : HTTPRequest, res : HTTPResponse):
        if req.method=="GET":
            if req.path.startswith(Server.SHARE_URL[:-1]):
                return self.handle_download(req, res)
            if req.path.startswith(Server.BROWSE_URL[:-1]):
                return self.handle_browse(req,res)
            return self.handle_www(req, res)

        if req.method=="POST":
            if req.path.startswith(Server.UPLOAD_URL[:-1]):
                return self.handle_upload(req, res)

        self.handle_404(req, res)

    def handle_www(self, req : HTTPRequest, res : HTTPResponse):
        #si le fichier n'existe pas
        path = conf.www(req.path[1:])
        if not os.path.isfile(path):
            return self.handle_404(req,res)

        res.serve_file(path)

    def handle_browse(self, req : HTTPRequest, res : HTTPResponse):
        relpath=req.path[len(Server.BROWSE_URL):]
        abspath = conf.share(relpath)
        if os.path.isdir(abspath):
            res.content_type("text/html")
            x=self.db.moustache(relpath)
            print(relpath)
            res.end(html_template(conf.www("index.html"),{
                "path" : relpath,
                "ls" : x,
                "parent" : os.path.normpath(relpath+"/..") if (len(relpath)>0) else "",
                "is_root" :  (len(relpath)==0)
            }))
            return
        self.handle_404(req,res)

    def handle_download(self, req : HTTPRequest, res : HTTPResponse):
        relpath=req.path[len(Server.SHARE_URL):]
        abspath = conf.share(relpath)

        #si le fichier n'existe pas
        if not os.path.isfile(abspath):
            return self.handle_404(req,res)

        res.serve_file(abspath, forceDownload=True)
        self.db.inc_download(relpath)

    def handle_upload(self, req : HTTPRequest, res : HTTPResponse):
        relapth=req.path[len(Server.UPLOAD_URL):]
        abspath=conf.SHARE_ABS_PATH
        if len(relapth): abspath+="/"+relapth
        x=req.multipart_next_file()
        while x:
            x.save(abspath)
            self.db.add(relapth, x.filename)
            x=req.multipart_next_file()

    def handle_404(self, req : HTTPRequest, res : HTTPResponse):
        res.code = 404
        res.msg = "Not Found"
        res.content_type("text/plain")
        res.end(req.path + " Not found")
