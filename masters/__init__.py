import ipaddress
import struct
from datetime import datetime

from database.orm import Game, Server
from database.functions import get_or_create


class Common():
    q2header = b'\xff\xff\xff\xff'
    q2header_ack = b''.join([q2header, b'ack'])
    q2header_servers = b''.join([q2header, b'servers '])
    q2header_ping = b''.join([q2header, b'ping'])
    q2header_heartbeat = b''.join([q2header, b'heartbeat'])
    q2query = b'query'

    @staticmethod
    def console_output(message):
        print(f"{datetime.utcnow().isoformat()}: {message}")


class Master(Common):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def bytepack(self, data):
        """
        Pack an IP (4 bytes) and Port (2 bytes) together
        IP addresses are stored as INET in Postgres
        Ports are stored as Integers in Postgres
        """
        ip = ipaddress.IPv4Address(data[0])
        port = data[1]
        return struct.pack('!LH', int(ip), port)

    @staticmethod
    def is_q2(data):
        command = data[:13]
        if command.startswith(Common.q2header_ping) or \
           command.startswith(Common.q2header_heartbeat) or \
           command.startswith(Common.q2query):
            return True
        else:
            return False


class Quake2(Master):
    def get_server(self, address):
        return self.session.query(Server)\
                           .filter_by(ip=address[0],
                                      port=address[1]).first()

    def process_heartbeat(self, address):
        self.console_output(f"Heartbeat from {address[0]}:{address[1]}")
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

        return None

    def process_shutdown(self, address):
        self.console_output(f"Shutdown from {address[0]}:{address[1]}")
        server = self.get_server(address)
        if server:
            server.active = False

        return None

    def process_ping(self, address):
        self.console_output(f"Sending ack to {address[0]}:{address[1]}")
        server = self.get_server(address)
        if server:
            server.active = True

        return Common.q2header_ack

    def process_query(self, address):
        self.console_output(f"Sending servers to {address[0]}:{address[1]}")
        serverstring = [Common.q2header_servers]
        for server in self.session.query(Server)\
                                  .filter(Server.active)\
                                  .with_entities(Server.ip,
                                                 Server.port).all():
            serverstring.append(self.bytepack(server))

        return b''.join(serverstring)

    def process_request(self, data, address):
        reply = None
        message = data.split(b'\n')
        if message[0].startswith(Common.q2header):
            command = message[0][4:]
            if command.startswith(b"heartbeat"):
                reply = self.process_heartbeat(address)
            elif command.startswith(b"shutdown"):
                reply = self.process_shutdown(address)
            elif command.startswith(b"ping"):
                reply = self.process_ping(address)
            else:
                self.console_output(f"Unknown command: {command}")
        elif message[0].startswith(b"query"):
            reply = self.process_query(address)
        else:
            self.console_output(f"Unable to process message")

        return reply
