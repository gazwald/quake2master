import ipaddress
import struct
import logging

from database.orm import Game, Server
from database.functions import get_or_create


class Headers():
    q2header = b'\xff\xff\xff\xff'
    q2header_ack = b''.join([q2header, b'ack'])
    q2header_servers = b''.join([q2header, b'servers '])
    q2header_ping = b''.join([q2header, b'ping'])
    q2header_shutdown = b''.join([q2header, b'shutdown'])
    q2header_heartbeat = b''.join([q2header, b'heartbeat'])
    q2query = b'query'


class Master():
    def __init__(self, session):
        self.session = session

    @classmethod
    def bytepack(cls, data):
        """
        Pack an IP (4 bytes) and Port (2 bytes) together
        IP addresses are stored as INET in Postgres
        Ports are stored as Integers in Postgres
        """
        ip_address = ipaddress.IPv4Address(data[0])
        port = data[1]
        return struct.pack('!LH', int(ip_address), port)

    @classmethod
    def is_q2(cls, data):
        command = data[:13]
        if command.startswith(Headers.q2header_ping) or \
           command.startswith(Headers.q2header_heartbeat) or \
           command.startswith(Headers.q2query):
            return True
        else:
            return False


class Quake2(Master):
    def __init(self, game):
        super().__init__()
        self.game = get_or_create(self.session, Game, name=game)

    def get_server(self, address):
        return self.session.query(Server)\
                           .filter_by(ip=address[0],
                                      port=address[1]).first()

    def process_heartbeat(self, address):
        logging.info(f"Heartbeat from {address[0]}:{address[1]}")
        server = self.get_server(address)
        if not server:
            server = Server(
                active=True,
                ip=address[0],
                port=address[1],
                game=self.game,
            )
            self.session.add(server)

        return None

    def process_shutdown(self, address):
        logging.info(f"Shutdown from {address[0]}:{address[1]}")
        server = self.get_server(address)
        if server:
            server.active = False

        return None

    def process_ping(self, address):
        logging.info(f"Sending ack to {address[0]}:{address[1]}")
        server = self.get_server(address)
        if server:
            server.active = True

        return Headers.q2header_ack

    def process_query(self, address):
        logging.info(f"Sending servers to {address[0]}:{address[1]}")
        serverstring = [Headers.q2header_servers]
        for server in self.session.query(Server)\
                                  .filter(Server.active)\
                                  .with_entities(Server.ip,
                                                 Server.port).all():
            serverstring.append(self.bytepack(server))

        return b''.join(serverstring)

    def process_request(self, data, address):
        reply = None
        message = data.split(b'\n')
        if message[0].startswith(Headers.q2header_heartbeat):
            reply = self.process_heartbeat(address)
        elif message[0].startswith(Headers.q2header_shutdown):
            reply = self.process_shutdown(address)
        elif message[0].startswith(Headers.q2header_ping):
            reply = self.process_ping(address)
        elif message[0].startswith(Headers.q2query):
            reply = self.process_query(address)
        else:
            logging.warning(f"Unknown message: {message}")

        return reply
