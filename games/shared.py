import ipaddress
import struct
import logging

from sqlalchemy import and_

from database.orm import Server


class Headers():
    """
    A collection of headers - not intended to be game specific
    """
    q2header = b'\xff\xff\xff\xff'
    # Master specific
    q2header_ack = b''.join([q2header, b'ack'])
    q2header_servers = b''.join([q2header, b'servers '])
    q2header_ping = b''.join([q2header, b'ping'])
    q2header_shutdown = b''.join([q2header, b'shutdown'])
    q2header_heartbeat = b''.join([q2header, b'heartbeat'])
    # Query specific
    q2query = b'query'
    q2header_query = b''.join([q2header, b'status 23\x0a'])
    q2header_print = b''.join([q2header, b'print'])


class idTechCommon():
    """
    Parent class, intended for functions that will be
    common among idtech servers
    """
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
        if command.startswith(Headers.q2header_ping) or \
           command.startswith(Headers.q2header_heartbeat) or \
           command.startswith(Headers.q2header_shutdown) or \
           command.startswith(Headers.q2query):
            return True

        return False


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

    @classmethod
    def is_q2(cls, data):
        """
        Determines if a specific request is a Quake 2 server or client
        """
        command = data[:13]
        if command.startswith(Headers.q2header_ping) or \
           command.startswith(Headers.q2header_heartbeat) or \
           command.startswith(Headers.q2header_shutdown) or \
           command.startswith(Headers.q2query):
            return True

        return False

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
        
        return Headers.q2header_ack

    def process_query(self, address):
        """
        Returns a list of servers (as bytes)
        For consumption by clients, eg: qstat
        """
        logging.info(f"Sending servers to {address[0]}:{address[1]}")
        if self.game.name == 'quake2':
            serverstring = [Headers.q2header_servers]
        else:
            serverstring = []

        for server in self.session.query(Server)\
                                  .filter(and_(Server.active,
                                               Server.game == self.game))\
                                  .with_entities(Server.ip,
                                                 Server.port).all():
            serverstring.append(self.bytepack(server))

        return b''.join(serverstring)
