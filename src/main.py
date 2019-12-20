from src import conf
from src.server import Server

serv = Server()
serv.listen(conf.LISTEN_PORT)