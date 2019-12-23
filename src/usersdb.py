
import os
import json
from src.user import User
import time
from src import conf

class UserDB:
    def __init__(self, js={}):
        self.db={}

        for x in js:
            obj=User(js[x])
            if obj.is_valid():
                self.db[x]=obj

    def find_user(self, id):
        if not id in self.db: return None
        obj=self.db[id]
        if obj.is_valid():
            return self.db[id]
        del self.db[id]
        return None

    def new_user(self, info):
        x=User.from_info(info)
        self.db[x.id]=x
        self.save()
        return x

    def save(self):
        js={}
        for k in self.db:
            js[k]=self.db[k].json()
        js=json.dumps(js)
        with open(conf.save("users.json"), "w") as f:
            f.write(js)

    def modify(self, id, js):
        client=id
        if isinstance(id, str):
            client=self.find_user(id)
        client.modify(js)
        self.save()

    def delete(self, id):
        del self.db[id]
        self.save()

    @staticmethod
    def load():
        path=conf.save("users.json")
        if os.path.isfile(path):
            with open(path, "r") as f:
                js=json.loads(f.read())
                return UserDB(js)
        return UserDB()

