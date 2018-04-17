import ipaddress
import struct
import logging

from sqlalchemy import and_

from database.orm import Server


class idTechCommon():
    """
    Parent class, intended for functions that will be
    common among idtech servers
    """

    common = b'\xff\xff\xff\xff'
    # Master specific
    headers = dict(
        quake2=dict(
            ack=b''.join([common, b'ack']),
            servers=b''.join([common, b'servers ']),
            ping=b''.join([common, b'ping']),
            shutdown=b''.join([common, b'shutdown']),
            heartbeat=b''.join([common, b'heartbeat']),
            query=b'query',
            server_query=b''.join([common, b'status 23\x0a']),
            server_print=b''.join([common, b'print'])
        )
    )

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
        """
        Determines if a specific request is a Quake 2 server or client
        """
        command = data[:13]
        return any(v for v in idTechCommon.headers['quake2'].values() if v.startswith(command))


class Master(idTechCommon):
    """
    Parent class, intended for functions that will be
    common among idtech servers
    """
    def __init__(self, session):
        self.session = session
        self.game = None

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

    def get_server(self, address):
        """
        Helper function - simply returns a server based on
        adress:port if it is known
        """
        return self.session.query(Server)\
                           .filter_by(ip=address[0],
                                      port=address[1],
                                      game=self.game).first()

    def process_heartbeat(self, address):
        """
        Processes a server heartbeat (not complete)
        Almost all data sent by a server heartbeat is
        currently discarded in favour of gathering it
        elsewhere
        """
        logging.info(f"Heartbeat from {address[0]}:{address[1]}")
        server = self.get_server(address)
        if not server:
            server = Server(
                active=True,
                ip=address[0],
                port=address[1],
                game=self.game
            )
            self.session.add(server)

        return None

    def process_shutdown(self, address):
        """
        Sets a server to inactive
        """
        logging.info(f"Shutdown from {address[0]}:{address[1]}")
        server = self.get_server(address)
        if server:
            server.active = False

        return None

    def process_ping(self, address):
        """
        Sets server to 'active' and
        Returns a ping acknowledgemnt
        """
        logging.info(f"Sending ack to {address[0]}:{address[1]}")
        server = self.get_server(address)
        if server:
            server.active = True

        return self.headers[self.game]['ack']

    def process_query(self, address):
        """
        Returns a list of servers (as bytes)
        For consumption by clients, eg: qstat
        """
        logging.info(f"Sending servers to {address[0]}:{address[1]}")
        if self.game.name == 'quake2':
            serverstring = [self.headers[self.game]['servers']]
        else:
            serverstring = []

        for server in self.session.query(Server)\
                                  .filter(and_(Server.active,
                                               Server.game == self.game))\
                                  .with_entities(Server.ip,
                                                 Server.port).all():
            serverstring.append(self.bytepack(server))

        return b''.join(serverstring)
