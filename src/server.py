import os
from .httpserver.restserver import Callback, HTTPRequest, HTTPResponse, HTTPServer
from src import conf
from os import path

class Server(HTTPServer):

    def __init__(self):
        HTTPServer.__init__(self, conf.LISTEN_HOST)


    def handlerequest(self, req : HTTPRequest, res : HTTPResponse):
        if req.method=="GET":
            if req.path.startswith(conf.SHARE_URL[:-1]):
                return self.handle_download(req, res)
            return self.handle_www(req, res)

        if req.method=="POST":
            return self.handle_upload(req, res)

        self.handle_404(req, res)

    def handle_www(self, req : HTTPRequest, res : HTTPResponse):
        #si le fichier n'existe pas
        path = conf.www(req.path[1:])
        if not os.path.isfile(path):
            return self.handle_404(req,res)

        res.serve_file(path)

    def handle_download(self, req : HTTPRequest, res : HTTPResponse):
        relpath=path.join(req.path[len(conf.SHARE_URL):])
        abspath = conf.share(relpath)

        #si le fichier n'existe pas
        if not os.path.isfile(abspath):
            return self.handle_404(req,res)

        res.serve_file(abspath, forceDownload=True)

    def handle_upload(self, req : HTTPRequest, res : HTTPResponse):
        x=req.multipart_next_file()
        while x:
            x.save(conf.SHARE_ABS_PATH)
            x=req.multipart_next_file()


    def handle_404(self, req : HTTPRequest, res : HTTPResponse):
        res.code = 404
        res.msg = "Not Found"
        res.content_type("text/plain")
        res.end(req.path + " Not found")
