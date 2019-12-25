import json
from .httpserver.utils import mime
import os
from src import conf
from .fileentry import new_from_fs, DirEntry
import json

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

    def modify(self, path, data):
        obj=self.find(path)
        obj.modify(data)

    def remove(self, path):
        if path[-1]=="/": path=path[:-1]
        path=path.split("/")
        parent=self.find('/'.join(path[:-1]))
        name=path[-1]

        parent = self.find(parent)
        obj = parent.children[name]
        if obj:
            obj.remove()
            del parent.children[name]
            self.save()
            return True
        return False

    def add(self, dir, name):
        objdir=self.find(dir)
        if objdir and objdir.isdir():
            objdir.add(name)
            self.save()

    def save(self):
        js=json.dumps(self.json())
        with open(conf.save("save.json"), "w") as f:
            f.write(js)

    @staticmethod
    def new_from_fs():
        return FileDB()

    @staticmethod
    def load():
        path = conf.save("save.json")
        if os.path.isfile(path):
            return FileDB(load=path)
        return FileDB.new_from_fs()
