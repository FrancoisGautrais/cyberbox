from src import conf
from src.server import Server
from src.fileentry import new_from_fs

serv = Server()
serv.listen(conf.LISTEN_PORT)