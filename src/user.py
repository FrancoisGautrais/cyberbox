
import time
from uuid import uuid4

def uuid():
    return str(uuid4()).replace("-","")[:16]

class User:
    DUREE_SESSION=60*24*30
    def __init__(self, js=None):
        self.id=""
        self.infos=""
        self.actions=0
        self.display="list"
        self.validity=time.time()+User.DUREE_SESSION
        if js:
            self._update(js)
        else:
            self.id=uuid()

    def _update(self, js):
        self.id=js["id"] if "id" in js else self.id
        self.actions=js["actions"] if "actions" in js else self.actions
        self.infos=js["infos"] if "infos" in js else self.infos
        self.validity=js["validity"] if "validity" in js else self.validity
        self.display=js["display"] if "display" in js else self.display


    def set_infos(self, infos):
        self.infos=infos

    def inc_actions(self):
        self.actions+=1

    def is_valid(self):
        return time.time()<self.validity

    def modify(self, js):
        self._update(js)

    def json(self):
        return {
            "id" : self.id,
            "actions" : self.actions,
            "infos" : self.infos,
            "validity": self.validity,
            "display": self.display,
        }

    @staticmethod
    def from_json(js):
        return User(js)

    @staticmethod
    def from_info(info):
        x=User()
        x.set_infos(info)
        return x
