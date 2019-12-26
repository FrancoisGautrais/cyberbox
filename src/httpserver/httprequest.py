import json
import io
import os
from .utils import mime
from .socketwrapper import SocketWrapper
from .formfile import FormFile
from src.httpserver.htmltemplate.htmlgen import html_gen

HTTP_OK=200
HTTP_BAD_REQUEST=400
HTTP_UNAUTHORIZED=401
HTTP_NOT_FOUND=404
HTTP_TEMPORARY_REDIRECT=307

STR_HTTP_ERROR={
    HTTP_OK: "OK",
    HTTP_UNAUTHORIZED: "Unauthorized",
    HTTP_BAD_REQUEST: "Bad request",
    HTTP_NOT_FOUND: "Not Found",
    HTTP_TEMPORARY_REDIRECT: "Temporary redirect"
}

def fromutf8(x): return bytes(x, "utf8")

def stripemptystr(p):
    out=[]
    for v in p:
        if v!='': out.append(v)
    return out



def testurl(template, url):
        url=stripemptystr(url.split("/"))
        template=stripemptystr(template.split("/"))
        args={}

        if len(url) != len(template): return None

        for i in range(0,len(template)):
            v=template[i]
            if v[0]=='#':
                args[v[1:]]=url[i]
            elif v!=url[i]: return None

        return args

BODY_DICT="dict"
BODY_EMPTY="none"
BODY_STRING="string"
BODY_FILE="file"
BODY_BYTES="bytes"

from urllib.parse import unquote

JSON_MIME=["application/json", "application/x-javascript", "text/javascript", "text/x-javascript", "text/x-json"]
URLENCODED_MIME= [ "application/x-www-form-urlencoded" ]
TEXT_MIME=["text/plain", "text/html", "text/javascript", "text/x-javascript", "text/x-json"]


def parse_urlencoded_params(string):
    out={}
    for k in string.split("&"):
        n = k.find("=")
        key = ""
        value = ""
        v = ""
        if n > 0:
            key = unquote(k[:n])
            value = unquote(k[n + 1:])
        else:
            key = unquote(k)
        out[key] = value
    return out

class _HTTP:

    def __init__(self):
        self._headers={}
        self.body=None
        self._body_type=BODY_EMPTY

    def body_type(self):
        return self._body_type

    def content_length(self, n:int=-1 ):
        x=self.header("Content-Length")
        return x if x else 0

    def content_type(self, x=None):
        if x:
            self.header("Content-Type", x)
            return x
        else: return self.header("Content-Type")


    def body_json(self):
        if self._body_type==BODY_DICT: return self.body
        raise Exception("Bad body format")

    def body_bytes(self):
        if self._body_type==BODY_BYTES: return self.body
        raise Exception("Bad body format")

    def body_text(self):
        if self._body_type==BODY_STRING: return self.body
        raise Exception("Bad body format")

    def body_file(self):
        if self._body_type==BODY_FILE: return self.body
        raise Exception("Bad body format")

class HTTPRequest(_HTTP):

    def __init__(self, socket, parse_headline=True):
        _HTTP.__init__(self)
        self.method=None
        self.version=""
        self.url="/"
        self.path="/"
        self.query={}
        self.params={}
        self.cookies={}
        self.filename=""
        self._head_line_parsed=parse_headline
        self._socket=socket

        if self._head_line_parsed:
            self._parse_command_line()

    def get_socket(self):
        return self._socket

    def header(self, key : str):
        if key in self._headers:
            return self._headers[key]
        return None


    def parse(self):
        self._parse_head()
        if ("Content-Type" in self._headers) and not self.header("Content-Type").startswith("multipart/form-data;"):
            self._parse_body()

    def multipart_next_file(self):

        ct = self.header("Content-Type")
        objct={}
        for x in ct.split(";"):
            if x.find("=")>0: objct[x[:x.find("=")].lstrip()]=x[x.find("=")+1:]
        boundary=objct["boundary"]
        f = FormFile(self._socket, boundary)
        if f.parse_head():
            return f
        return None

    def _parse_head(self):
        #parse 1st line if it is not done
        if not self._head_line_parsed :
            self._parse_command_line()

        # parse all headers
        line = self._socket.readline()[:-1]
        while len(line)>0:
            key=line[:line.find(":")]
            val=line[line.find(":")+1:].lstrip()
            self._set_header(key, val)
            line=self._socket.readline()[:-1]

    def _parse_body(self):
        l=self.content_length()
        if not l:
            self._body_type=BODY_EMPTY
            self.body=bytes()

        ct = "application/octet-stream"
        cl=0
        try:
            ct = self.header("Content-Type").split(';')[0].rstrip().lower()
        except: pass

        try:
            cl = int(self.header("Content-Length"))
        except: pass

        if ct in JSON_MIME:
            self._body_type=BODY_DICT
            content=self._socket.read(cl).decode("utf8")
            self.body=json.loads(content)
        elif ct in URLENCODED_MIME:
            self._body_type=BODY_DICT
            self.body=parse_urlencoded_params(self._socket.read(cl).decode("utf8"))
        elif ct in TEXT_MIME:
            self._body_type=BODY_STRING
            self.body=self._socket.read(cl).decode("utf8")
        else:
            self._body_type=BODY_BYTES
            self.body=self._socket.read(cl)



    def _set_header(self, key : str, val):
        if val and key.lower()=="cookie":
            clist = val.split(";")
            for x in clist:
                x = x.split("=")
                k = x[0].rstrip()
                v = x[1].lstrip() if len(x) > 1 else ""
                self.cookies[k] = v
        self._headers[key]= val

    def _parse_command_line(self):
        self._head_line_parsed = True

        head=self._socket.readline()[:-1].split(" ")
        self.method=head[0]
        self.url=head[1]
        self.version=head[2]


        self.path=self.url
        n=self.url.find("?")

        if n>=0:
            self.path=self.url[:n]
            tmp=self.url[n+1:]
            self.query=parse_urlencoded_params(tmp)
            self.filename=os.path.basename(self.path)



class HTTPResponse(_HTTP):

    def __init__(self, code=200):
        _HTTP.__init__(self)
        self.version = "HTTP/1.1"
        self.code=code
        self.msg=STR_HTTP_ERROR[code]


    def header(self, key : str, val):
        self._headers[key]=val

    def end(self, data):
        self.body=data
        if isinstance(data, str):
            self._body_type=BODY_STRING
        elif isinstance(data, bytes):
            self._body_type=BODY_BYTES
        elif isinstance(data, dict):
            self._body_type=BODY_DICT
        elif isinstance(data, io.BufferedIOBase):
            self._body_type=BODY_FILE
        else:
            self._body_type=BODY_EMPTY

    def serve_file_gen(self, path : str, data):
        self.content_type(mime(path))
        self.header("Content-Length", str(os.stat(path).st_size))
        self.header("Content-Type", mime(path))
        self.end(html_gen(path, data))


    def serve_file(self, path : str, urlReq=None, forceDownload=False, data={}):
        if path.endswith(".html"):
            return self.serve_file_gen(path, data)

        fd=None
        try:
            fd=open(path, "rb")
        except Exception as err:
            self.code = HTTP_NOT_FOUND
            self.msg = STR_HTTP_ERROR[HTTP_NOT_FOUND]
            self.content_type("text/plain")
            if urlReq:
                self.end(str(urlReq)+" not found")
            else:
                self.end("File not found : "+str(err))
            return

        #self._isStreaming=True
        self.content_type(mime(path))
        self.header("Content-Length", str(os.stat(path).st_size))
        self.header("Content-Type", mime(path))

        if forceDownload:
            self.header("Content-Disposition", "attachment; filename=\""+\
                    os.path.basename(path)+"\"")
        with open(path, "rb") as f:
            self.end(f.read())
        #self.end(open(path, "rb"))

    def _set_json_response(self, httpcode : int, code : int , msg : str, js):
        self.header("Content-Type", "application/json")
        self.code = httpcode
        self.msg = STR_HTTP_ERROR[httpcode]
        self.end(bytes(json.dumps({"code": code, "message": msg, "data": js}), "utf8"))

    def ok(self, code : int, msg : str, js):
        self._set_json_response(HTTP_OK, code, msg, js)

    def unauthorized(self, code : int, msg : str, js):
        self._set_json_response(HTTP_UNAUTHORIZED, code, msg, js)

    def bad_request(self, code : int, msg : str, js):
        self._set_json_response(HTTP_BAD_REQUEST, code, msg, js)

    def not_found(self, code : int, msg : str, js):
        self._set_json_response(HTTP_NOT_FOUND, code, msg, js)

    def temporary_redirect(self, url : str):
        self.code = HTTP_TEMPORARY_REDIRECT
        self.msg = STR_HTTP_ERROR[HTTP_TEMPORARY_REDIRECT]
        self.header("Location", url)
        self.end("")

    def write(self, soc : SocketWrapper):
        out=None
        typ=self.body_type()
        if typ==BODY_DICT:
            out=bytes(json.dumps(self.body), "utf8")
        elif typ==BODY_BYTES:
            out=self.body
        elif typ==BODY_STRING:
            out=bytes(self.body, "utf8")
        else: out=bytes()

        self.header("Content-Length", len(out))
        soc.send(fromutf8(self.version + " " + str(self.code) + " " + self.msg + "\r\n"))
        for k in self._headers:
            soc.send(fromutf8(k + ": " + str(self._headers[k]) + "\r\n"))
        soc.send(fromutf8("\r\n"))

        soc.send(out)


