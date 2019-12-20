
from .socketwrapper import SocketWrapper
from src import conf
from os import  path


class FormFile:

    def __init__(self, soc : SocketWrapper, boundary : str):
        self.soc=soc
        self.boundary=bytes("--"+boundary, "ascii")
        self.filename=""
        self.mime=""
        self.attrs={}

    def parse_head(self):
        bound=self.soc.readline()
        if bound.endswith("--\r") : return False
        head=self.soc.readline()[:-1]
        head+="\n"+self.soc.readline()[:-1]
        head=head.split("\n")
        for h in head:
            tmp=h.split(":")
            key = tmp[0]
            val = tmp[1][1:]
            if val.find(";")>0:
                v={}
                for k in val.split(";"):
                    k=k.lstrip()
                    if k.find("=")>0:
                      v[k[:k.find("=")]]=k[k.find("=")+1:]
                    else: v[k]=None
                val=v
            self.attrs[key]=val
        self.soc.readline()
        return True
    NO_BOUND=0
    SIMPLE_BOUND=1
    END_BOUND=2
    #
    #
    #
    def is_bound(self):
        tmp = self.soc.read(len(self.boundary))
        self.soc.rewind(tmp)
        if tmp != self.boundary:
            return FormFile.NO_BOUND
        if self.soc.read(2) == bytes("\r\n", "ascii"): return FormFile.SIMPLE_BOUND
        self.soc.read(2)
        return FormFile.END_BOUND


    def save(self, p):
        out=path.normpath(conf.share(p)+"/"+self.attrs["Content-Disposition"]["name"])
        print(out)
        with open(out, "wb") as f:
            x=self.soc.read(1)
            while True:
                f.write(x)
                x=self.soc.read(1)
                if x==bytes("\n", "ascii"):
                    bound=self.is_bound()

                    if bound==FormFile.END_BOUND:
                        return False
                    elif bound == FormFile.SIMPLE_BOUND:
                        return True