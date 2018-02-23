import ipaddress
import struct

from database.orm import Game, Server
from database.functions import get_or_create


class Master:
    def __init__(self, session):
        self.header = b'\xff\xff\xff\xff'
        self.header_ack = b''.join([self.header, b'ack'])
        self.header_servers = b''.join([self.header, b'servers '])
        self.session = session

    @staticmethod
    def bytepack(data):
        """
        Pack an IP (4 bytes) and Port (2 bytes) together
        IP addresses are stored as INET in Postgres
        Ports are stored as Integers in Postgres
        """
        ip = ipaddress.IPv4Address(data[0])
        port = data[1]
        return struct.pack('!LH', int(ip), port)


class Quake2(Master):
    def fetch_servers(self):
        serverstring = [self.header_servers]
        for server in self.session.query(Server)\
                                  .filter(Server.active)\
                                  .with_entities(Server.ip,
                                                 Server.port).all():
            serverstring.append(self.bytepack(server))

        return b''.join(serverstring)

    def get_server(self, address):
        return self.session.query(Server, address)\
                           .filter_by(ip=address[0],
                                      port=address[1]).first()

    def process_heartbeat(self, address):
        self.game = get_or_create(self.session, Game, name='q2')
        server = self.get_server(address)
        if not server:
            server = Server(
                active=True,
                ip=address[0],
                port=address[1],
                game=self.game,
            )
            self.session.add(server)

    def process_shutdown(self, address):
        server = self.get_server(address)
        if server:
            server.active = False

    def process_ping(self, address):
        server = self.get_server(address)
        if server:
            server.active = True
        return self.header_ack

    def process_query(self):
        return self.fetch_servers()
