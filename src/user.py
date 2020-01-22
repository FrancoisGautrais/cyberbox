import json
import time
from uuid import uuid4

from src.http_server import log


def uuid():
    return str(uuid4()).replace("-","")[:16]

class User:
    DUREE_SESSION=60*24*30
    def __init__(self, js=None):
        self.id=""
        self.infos=""
        self.actions=0
        self.admin=False
        self.display="list"
        self.sort="name"
        self.order="inc"
        self.validity=time.time()+User.DUREE_SESSION
        self.name=None
        if js:
            self._update(js)
        else:
            self.id=uuid()

    def _update(self, js):
        self.id=js["id"] if "id" in js else self.id
        self.name=js["name"] if "name" in js else self.name
        self.actions=js["actions"] if "actions" in js else self.actions
        self.infos=js["infos"] if "infos" in js else self.infos
        self.validity=js["validity"] if "validity" in js else self.validity
        self.admin=js["admin"] if "admin" in js else self.admin
        self.display=js["display"] if "display" in js else self.display
        self.sort=js["sort"] if "sort" in js else self.sort
        self.order=js["order"] if "order" in js else self.order

    def is_admin(self):
        return self.admin

    def set_infos(self, infos):
        self.infos=infos

    def set_name(self, name):
        self.name=name

    def inc_actions(self):
        self.actions+=1

    def is_valid(self):
        return time.time()<self.validity

    def modify(self, js):
        self._update(js)


    def is_mobile(self):
        try:
            return ("Mobi" in self.infos)# or ("iPhone" in self.infos) or ("Android" in self.infos)
        except:
            log.error("user::is_mobile(), self.infos = "+str(self.infos))

    def json(self):
        return {
            "id" : self.id,
            "name" : self.name,
            "actions" : self.actions,
            "infos" : self.infos,
            "validity": self.validity,
            "display": self.display,
            "order": self.order,
            "sort": self.sort,
            "admin": self.admin,
            "mobile" : self.is_mobile()
        }

    @staticmethod
    def from_json(js):
        return User(js)

    @staticmethod
    def from_info(info, name=None):
        x=User()
        x.set_infos(info)
        x.set_name(name)
        return x
