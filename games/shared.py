import ipaddress
import struct


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
