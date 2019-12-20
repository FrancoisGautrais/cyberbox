from .socketwrapper import SocketWrapper, ServerSocket
from .httprequest import HTTPResponse, HTTPRequest, testurl, HTTP_OK, STR_HTTP_ERROR, HTTP_NOT_FOUND
from .utils import Callback, start_thread

import os
import time


class HTTPServer(ServerSocket):

    def __init__(self, ip="localhost"):
        ServerSocket.__init__(self)
        self._ip=ip


    def listen(self, port):
        self._port = port
        self.bind(self._ip, self._port)
        while True:
            x=super().accept()
            req = HTTPRequest(x)
            start_thread( Callback(HTTPServer._handlerequest, self, req))

    def _handlerequest(self, req : HTTPRequest):
        req.parse()
        res=HTTPResponse(200, )
        x=time.time()*1000
        self.handlerequest(req, res)

        res.write(req.get_socket())
        req.get_socket().close()

    def handlerequest(self, req, res):
        pass


    def serve_file(self, req: HTTPRequest, res : HTTPResponse):
        res.serve_file(os.path.join(self.www_dir, req.path[1:]))
