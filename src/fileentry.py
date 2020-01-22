from src import conf, error
import os
from src.http_server.utils import mime_to_type

from src.http_server import log
from src.http_server.filecache import filecache

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


class Meta:
    AUTEUR="Auteur"
    TITRE="Titre"


class _Entry:
    DIRECTORY="dir"
    FILE="file"
    F_CREATION="creation"
    F_NAME="name"
    F_TYPE="type"
    F_DIR="dir"
    F_META="meta"
    #
    # String h: hidden, r: can read, w: can write
    #
    F_ATTRS="attrs"


    def __init__(self, type, dir, js):
        self.dir=dir
        self.type=type if type else js[_Entry.F_NAME]
        self.creation=_attr(js, _Entry.F_CREATION, -1)
        self.name=_attr(js, _Entry.F_NAME, "")
        self.attrs=_attr(js, _Entry.F_ATTRS, "hrw" if len(self.name)>0 and self.name[0]=="." else "rw")
        self.meta=_attr(js, _Entry.F_META, {})

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
            _Entry.F_DIR: self.dir,
            _Entry.F_CREATION: self.creation,
            _Entry.F_TYPE: self.type,
            _Entry.F_ATTRS: self.attrs,
            _Entry.F_META: self.meta
        }

    def can_read(self, isAdmin):
        return "r" in self.attrs or isAdmin

    def can_write(self, isAdmin):
        return "w" in self.attrs or isAdmin

    def is_hidden(self, isAdmin): return ("h" in self.attrs) and not isAdmin

    def moustache(self, recursive=False, showHdden=False):
        x=_Entry.json(self)
        x["dir"]=self.dir+("/" if len(self.dir)>0 else "")
        x["url_prefix"]="/browse/" if self.isdir() else "/share/"
        x["path"] = os.path.join(self.dir, self.name) if len(self.dir)>0 else self.name
        x["is_dir"]=self.isdir()
        x["attrs"]=self.attrs
        return x

    def update(self, isAdmin):
        raise Exception("Must be implemented")

    def _update(self, stat):
        self.creation=stat.st_ctime
        return error.ERR_OK

    def isdir(self):
        return self.type==_Entry.DIRECTORY

    def modify(self, data, isAdmin):
        if not self.can_write(isAdmin): return error.ERR_FORBIDDEN
        if FileEntry.F_ATTRS in data: self.attrs=data[FileEntry.F_ATTRS]
        return error.ERR_OK

    def search(self, search, isadmin, results=[]):
        match = search["match"].lower() if "match" in search else None
        if self.is_hidden(isadmin): return False
        if match and not (match in self.name.lower()): return False
        return True

class FileEntry(_Entry):
    F_SIZE="size"
    F_MIME="mime"
    F_DOWNLOAD="download"

    def __init__(self, path, js, update=False):
        _Entry.__init__(self, _Entry.FILE,  path, js)
        self.size=_attr(js, FileEntry.F_SIZE, -1)
        self.mime=_attr(js, FileEntry.F_MIME, None)
        self.download=_attr(js, FileEntry.F_DOWNLOAD, 0)
        if update: self.update(True)
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

    def info(self, isAdmin):
        return self.json()

    def update(self, isAdmin):
        if not self.can_write(isAdmin): return error.ERR_FORBIDDEN
        stat=os.stat(self.abspath)
        _Entry._update(self, stat)
        self.size=stat.st_size
        #self.mime=filecache.mime(self.abspath)
        return error.ERR_OK

    def remove(self, isAdmin):
        if not self.can_write(isAdmin): return error.ERR_FORBIDDEN
        try:
            os.remove(self.abspath)
            return error.ERR_OK
        except:
            return error.ERR_NOT_FOUND

    def modify(self, data, isAdmin):
        if not self.can_write(isAdmin): return error.ERR_FORBIDDEN
        _Entry.modify(self, data, isAdmin)
        if FileEntry.F_DOWNLOAD in data: self.download=data[FileEntry.F_DOWNLOAD]
        return error.ERR_OK


    def search(self, search, isadmin, results=[]):
        if _Entry.search(self, search, isadmin, results ):
            types = search["types"] if "types" in search else None
            if types and not (mime_to_type(self.mime) in types): return
            results.append(self.moustache(False, isadmin))

class DirEntry(_Entry):
    F_CHILDREN="children"

    def __init__(self, path, js, update=False):
        _Entry.__init__(self, _Entry.DIRECTORY, path, js)
        self.children={}
        for child in _attr(js, DirEntry.F_CHILDREN, []):
            self.children[child[_Entry.F_NAME]]=new_from_js(self.relpath, child)
        if update: self.update(True)

    def json(self):
        ret=_Entry.json(self)
        children=[]
        for child in self.children:
            children.append(self.children[child].json())
        ret[DirEntry.F_CHILDREN]=children
        return ret

    def modify(self, data, isAdmin):
        return _Entry.modify(self, data, isAdmin)

    def moustache(self, first=True, showHdden=False):
        if not first:
            ret = _Entry.moustache(self, showHdden)
            ret["length"]=len(self.children)
            return ret
        else:
            children=[]
            for child in self.children:
                if (not self.children[child].is_hidden(showHdden)) :
                    children.append(self.children[child].moustache(False, showHdden))
            return children

    def info(self, isAdmin):
        x=_Entry.json(self)
        x["length"]=len(self.children)
        return x

    def remove(self, isAdmin):
        if not self.can_write(isAdmin): return error.ERR_FORBIDDEN
        for f in self.children:
            self.children[f].remove(isAdmin)
        os.rmdir(self.abspath)
        return error.ERR_OK

    def add(self, name, force=False):
        if not force and (name in self.children): return False
        self.children[name]=new_from_fs(self.relpath, name)
        return True

    def update(self, isAdmin):
        if not self.can_write(isAdmin): return error.ERR_FORBIDDEN
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
                else: obj.update(isAdmin)

            #le fichier/dossier n'existe pas
            else:
                self.add(name)

        #on vérifie que tous les fichiers de la base existent sur le disque
        for name in self.children:
            if not name in children:
                del self.children[name]
        if not self.can_write(isAdmin): return error.ERR_OK

    def search(self, search, isadmin, results=[]):
        if _Entry.search(self, search, isadmin, results ):
            types = search["types"] if "types" in search else None
            if types and not ("dir" in types):
                results.append(self.moustache(False, isadmin))

        if self.can_read(isadmin):
            for name in self.children:
                self.children[name].search(search, isadmin, results)
        return results