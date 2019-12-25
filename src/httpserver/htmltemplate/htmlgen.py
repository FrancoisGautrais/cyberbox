from src.utils import html_template_string
from src.httpserver.htmltemplate.lexer import Lexer






class Instruction:

    def __init__(self, fd, data, revert=None, lex=None):
        self.lex=Lexer(fd, data) if not lex else lex
        self.data=data
        self.inst=""
        self.args=[]

        if revert:
            self.inst=revert
        else:
            curr=self.lex.next()
            if curr!=Lexer.IDENT: raise Exception("Parser error expected ident found :", curr)
            self.inst=self.lex.value

        curr=self.lex.next()
        if curr!=Lexer.P_OUVRANTE: raise Exception("Parser error expected '(' found :", curr)

        curr=self.lex.next()
        if curr!=Lexer.P_FERMANTE:
            curr=self._next_value()
            while curr==Lexer.VIRGULE:
                self.lex.next()
                curr=self._next_value()

        if curr!=Lexer.P_FERMANTE: raise Exception("Parser error expected ')' found :", curr)




    def _next_value(self):
        if self.lex.current in [Lexer.INT, Lexer.FLOAT, Lexer.STRING]:
            self.args.append(self.lex.value)
            self.lex.next()
        elif self.lex.current==Lexer.IDENT:
            inst = Instruction(self.lex.fd, self.data, self.lex.value, self.lex)
            self.args.append(inst.value())
            self.lex.next()
        else:
            raise Exception("Parser error expected int, float, string or ident, found :",self.lex.current)
        return self.lex.current


    def value(self):
        if self.inst=="include":
            with open(self.args[0]) as f:
                return f.read()

        if self.inst=="get":
            acc=self.data
            for x in self.args:
                acc=acc[x]
            return acc

        if self.inst=="cat":
            acc=""
            for x in self.args:
                acc+=str(x)
            return acc
        raise Exception("Error unknown instruction '",self.inst,"'")

class HtmlGen:

    def __init__(self, filename, isFile=True):
        self.fd=open(filename, "r")
        self.text=""
        self.c=""

    def close(self):
        self.close()

    def _read(self):
        self.c=self.fd.read(1)
        return self.c

    def _read_next(self, data):
        x=" "
        while x!="":
            x = self._read()
            while x!="" and x!="<":
                self.text+=x
                x=self._read()
            if x=="<":
                x=self._read()
                if x=="#":
                    return Instruction(self.fd, data)
                else: self.text+="<"+x
        return None


    def _replace_next(self, data):
        inst=self._read_next(data)
        if inst:
            self.text+=str(inst.value())
            return True
        return False

    def gen(self, data):
        x=True
        while x:
            x=self._replace_next(data)
        self.fd.close()
        return self.text


def html_gen(filename, data):
    x = HtmlGen(filename)
    content=x.gen(data)
    return html_template_string(content,data)
