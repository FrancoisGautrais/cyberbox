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

    def moustache(self, path=""):
        obj = self.find(path)
        if obj:
            return obj.moustache()
        return None

    def inc_download(self, path, n=1):
        obj=self.find(path)
        if obj and not obj.isdir():
            obj.download+=1
            self.save()
            return True
        else:
            return False

    def remove(self, path):
        obj = self.find(path)
        if obj:
            obj.remove()
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
