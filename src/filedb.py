import json
import os
from src import conf
from .fileentry import new_from_fs, DirEntry
import json

from src import error

class FileDB:


    def __init__(self, load=None):
        if not load:
            self.db=DirEntry("",{}, True)
        else:
            with open(load) as f:
                self.db=DirEntry("",json.loads(f.read()), True)

    def find(self, path):
        return self.db.find(path)


    def json(self, path=""):
        obj = self.find(path)
        if obj: return obj.json()
        return None

    def moustache(self, path="", isAdmin=False):
        obj = self.find(path)
        if obj:
            return obj.moustache(showHdden=isAdmin)
        return None

    def inc_download(self, path, n=1):
        obj=self.find(path)
        if obj and not obj.isdir():
            obj.download+=1
            self.save()
            return True
        else:
            return False

    def modify(self, path, data, isAdmin):
        obj=self.find(path)
        x=obj.modify(data, isAdmin)
        self.save()
        return x

    def remove(self, path, isAdmin):
        if path[-1]=="/": path=path[:-1]
        path=path.split("/")
        parent=self.find('/'.join(path[:-1]))
        name=path[-1]

        obj = parent.children[name]
        if obj:
            x=obj.remove(isAdmin)
            del parent.children[name]
            self.save()
            return x
        return error.ERR_NOT_FOUND

    def search(self, search, isadmin):
        return self.db.search(search, isadmin, [])

    def add(self, dir, name):
        objdir=self.find(dir)
        ret=True
        if objdir and objdir.isdir():
            r=objdir.add(name)
            if not r: return r
            self.save()
        return error.ERR_OK

    def mkdir(self, path, isAdmin, attr):
        pathl=path.split("/")
        dir=pathl[:-1]
        name=pathl[-1]
        os.mkdir(conf.share(path))
        x=self.add(dir, name)
        if attr:
            obj=self.find(path)
            return obj.modify(attr, isAdmin)
        return x



    def save(self):
        js=json.dumps(self.json())
        with open(conf.save("save.json"), "w") as f:
            f.write(js)
            return error.ERR_OK

    @staticmethod
    def new_from_fs():
        return FileDB()

    @staticmethod
    def load():
        path = conf.save("save.json")
        if os.path.isfile(path):
            return FileDB(load=path)
        return FileDB.new_from_fs()
