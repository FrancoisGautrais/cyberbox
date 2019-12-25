from src import conf
import os
from .httpserver.utils import mime

def _attr(obj, key, default):
    return obj[key] if (key in obj) else default

def new_from_js(dir, js):
    if _Entry.F_TYPE in js:
        type=js[_Entry.F_TYPE]
        if type==_Entry.DIRECTORY:
            return DirEntry(dir, js)
        elif type==_Entry.FILE:
            return FileEntry(dir, js)
    raise Exception("Error no type specified")

def new_from_fs(dir, name):
    rel = os.path.join(dir, name)
    absp = conf.share(rel)
    if os.path.isdir(absp):
        return DirEntry(dir, {"name":name}, True)
    elif os.path.isfile(absp):
        return FileEntry(dir, {"name":name}, True)
    else:
        raise Exception("Error ",absp, ": not a file and not a directory")


class _Entry:
    DIRECTORY="dir"
    FILE="file"
    F_CREATION="creation"
    F_NAME="name"
    F_TYPE="type"
    F_HIDDEN="hidden"

    def __init__(self, type, dir, js):
        self.dir=dir
        self.type=type if type else js[_Entry.F_NAME]
        self.creation=_attr(js, _Entry.F_CREATION, -1)
        self.name=_attr(js, _Entry.F_NAME, "")
        self.hidden=_attr(js, _Entry.F_HIDDEN, True if len(self.name)>0 and self.name[0]=="." else False)

        self.reldir=self.dir
        self.relpath=os.path.join(self.reldir, self.name)
        self.abspath=conf.share(self.relpath)
        self.absdir=conf.share(self.reldir)

    def find(self, path):
        if isinstance(path, str): path=path.split("/")
        it=self
        for name in path:
            if len(name)>0 and it.isdir():
                it=it.children[name]
        return it

    def json(self):
        return {
            _Entry.F_NAME: self.name,
            _Entry.F_CREATION: self.creation,
            _Entry.F_TYPE: self.type,
            _Entry.F_HIDDEN: self.hidden
        }

    def moustache(self, recursive=False, showHdden=False):
        x=_Entry.json(self)
        x["dir"]=self.dir+("/" if len(self.dir)>0 else "")
        x["url_prefix"]="/browse/" if self.isdir() else "/share/"
        x["is_dir"]=self.isdir()
        x["hidden"]=self.hidden
        return x

    def update(self):
        raise Exception("Must be implemented")

    def _update(self, stat):
        self.creation=stat.st_ctime

    def isdir(self):
        return self.type==_Entry.DIRECTORY

    def modify(self, data):
        if FileEntry.F_HIDDEN in data: self.hidden=data[FileEntry.F_HIDDEN]

class FileEntry(_Entry):
    F_SIZE="size"
    F_MIME="mime"
    F_DOWNLOAD="download"

    def __init__(self, path, js, update=False):
        _Entry.__init__(self, _Entry.FILE,  path, js)
        self.size=_attr(js, FileEntry.F_SIZE, -1)
        self.mime=_attr(js, FileEntry.F_MIME, None)
        self.download=_attr(js, FileEntry.F_DOWNLOAD, 0)
        if update: self.update()

    def json(self):
        ret=_Entry.json(self)
        ret.update({
            FileEntry.F_SIZE: self.size,
            FileEntry.F_MIME: self.mime,
            FileEntry.F_DOWNLOAD: self.download,
        })
        return ret

    def moustache(self, recursive=False, showHdden=False):
        ret=_Entry.moustache(self)
        ret.update({
            FileEntry.F_SIZE: self.size,
            FileEntry.F_MIME: self.mime,
            FileEntry.F_DOWNLOAD: self.download
        })
        return ret

    def update(self):
        stat=os.stat(self.abspath)
        _Entry._update(self, stat)
        m=mime(self.abspath)
        self.size=stat.st_size
        self.mime=mime(self.abspath)

    def remove(self):
        os.remove(self.abspath)

    def modify(self, data):
        _Entry.modify(self, data)
        if FileEntry.F_DOWNLOAD in data: self.download=data[FileEntry.F_DOWNLOAD]

class DirEntry(_Entry):
    F_CHILDREN="children"

    def __init__(self, path, js, update=False):
        _Entry.__init__(self, _Entry.DIRECTORY, path, js)
        self.children={}
        for child in _attr(js, DirEntry.F_CHILDREN, []):
            self.children[child[_Entry.F_NAME]]=new_from_js(self.relpath, child)
        if update: self.update()

    def json(self):
        ret=_Entry.json(self)
        children=[]
        for child in self.children:
            children.append(self.children[child].json())
        ret[DirEntry.F_CHILDREN]=children
        return ret

    def modify(self, data):
        _Entry.modify(self, data)

    def moustache(self, first=True, showHdden=False):
        if not first:
            ret = _Entry.moustache(self, showHdden)
            ret["length"]=len(self.children)
            return ret
        else:
            children=[]
            for child in self.children:
                if not self.children[child].hidden or showHdden:
                    children.append(self.children[child].moustache(False, showHdden))
            return children

    def remove(self):
        for f in self.children:
            f.remove()
        os.rmdir(self.abspath)

    def add(self, name, force=False):
        if not force and (name in self.children): raise Exception("Error child exists !")
        self.children[name]=new_from_fs(self.relpath, name)

    def update(self):
        _Entry._update(self, os.stat(self.abspath))
        children=os.listdir(self.abspath)

        #on vérifie que tous les fichier du disque sont dans la base
        for name in children:
            # si le fichier/dossier existe dans la base
            if name in self.children:
                obj=self.children[name]
                type=os.path.isdir(obj.abspath)

                #si le type (fichier ou dossier) ne correspond pas
                if type and not obj.isdir():
                    self.add(name, force=True)

                #si le type correspond
                else: obj.update()

            #le fichier/dossier n'existe pas
            else: self.add(name)

        #on vérifie que tous les fichiers de la base existent sur le disque
        for name in self.children:
            if not name in children:
                del self.children[name]

