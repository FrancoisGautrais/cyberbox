
import os
import json

from src.http_server import log
from src.user import User
import time
from src import conf
from src.http_server.utils import sha256

class UserDB:
    def __init__(self, js={}):
        with open(conf.base("conf/users.json")) as f:
            self.auth=json.loads(f.read())
        self.db={}

        for x in js:
            obj=User(js[x])
            if obj.is_valid():
                self.db[x]=obj

    def authentification(self, basic):
        for user in self.auth:
            pas=sha256(user+":"+self.auth[user]["password"]).hex()
            if pas==basic:
                return user
        return None

    def find_user(self, id):
        if not id in self.db: return None
        obj=self.db[id]
        if obj.is_valid():
            return self.db[id]
        del self.db[id]
        return None

    def new_user(self, info, user=None):
        x=User.from_info(info, user)
        if user in self.auth and self.auth[user]:
            x.admin=self.auth[user].admin
        self.db[x.id]=x
        self.save()
        return x

    def set_name(self, id, name):
        x = None
        if id in self.db:
            x = self.db[id]
        if x and name in self.auth and self.auth[name]:
            x.admin=self.auth[name]["admin"]
        else:
            x.admin=False
        self.save()


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

