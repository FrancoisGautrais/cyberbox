from src.utils import html_template_string

class _Inst:

    def __init__(self, fd):
        self.inst=""
        self.args=[]

        x=fd.read(1)
        while x!="(" and x!=":":
            self.inst+=x
            x=fd.read(1)
        while x!="" and x!=")":
            x=fd.read(1)
            while x!=")" and x!="":
                args = ""
                while x!=")" and x!="," and x!="":
                    args+=x
                    x=fd.read(1)
                if len(args)>0: self.args.append(args)
        while x!=">" and x!="":
            x=fd.read(1)

class HtmlGen:

    def __init__(self, filename):
        self.fd=open(filename, "r")
        self.text=""
        self.c=""

    def close(self):
        self.close()

    def _read(self):
        self.c=self.fd.read(1)
        return self.c

    def _read_next(self):
        x=" "
        while x!="":
            x = self._read()
            while x!="" and x!="<":
                self.text+=x
                x=self._read()
            if x=="<":
                x=self._read()
                if x=="#":
                    return _Inst(self.fd)
                else: self.text+="<"+x
        return None


    def _replace_next(self):
        inst=self._read_next()
        if inst:
            if inst.inst=="include":
                with open(inst.args[0]) as f:
                    self.text+=f.read()
            else: raise Exception("Insctruction '"+inst.inst+"' inconnu")
            return True
        return False

    def gen(self):
        x=True
        while x:
            x=self._replace_next()
        self.fd.close()
        return self.text


def html_gen(filename, data):
    x = HtmlGen(filename)
    content=x.gen()
    return html_template_string(content,data)