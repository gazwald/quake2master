#!/usr/bin/env python3
import asyncio
import ipaddress
import struct
from datetime import datetime

from database.orm import Game, Server
from database.functions import (get_or_create,
                                create_db_session,
                                create_db_conn)


class MasterServer:
    def __init__(self):
        self.header = b'\xff\xff\xff\xff'
        self.header_ack = b''.join([self.header, b'ack'])
        self.header_stat = b''.join([self.header, b'stat'])
        self.header_servers = b''.join([self.header, b'servers '])

    @staticmethod
    def console_output(message):
        print(f"{datetime.utcnow().isoformat()}: {message}")

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

    def fetch_servers(self):
        serverstring = [self.header_servers]
        for server in session.query(Server)\
                             .filter(Server.active)\
                             .with_entities(Server.ip,
                                            Server.port).all():
            serverstring.append(self.bytepack(server))

        return b''.join(serverstring)

    def get_server(self):
        return session.query(Server)\
                      .filter_by(ip=self.origin[0],
                                 port=self.origin[1]).first()

    def connection_made(self, transport):
        self.transport = transport

    def process_heartbeat(self, name):
        self.console_output(f"Heartbeat from {self.origin[0]}:{self.origin[1]}")
        self.game = get_or_create(session, Game, name=name)
        server = self.get_server()
        if not server:
            server = Server(
                active=True,
                ip=self.origin[0],
                port=self.origin[1],
                game=self.game,
            )
            session.add(server)

    def process_shutdown(self):
        self.console_output(f"Shutdown from {self.origin[0]}:{self.origin[1]}")
        server = self.get_server()
        if server:
            server.active = False

    def process_ping(self):
        self.console_output(f"Sending ack to {self.origin[0]}:{self.origin[1]}")
        server = self.get_server()
        if server:
            server.active = True
        self.transport.sendto(self.header_ack, self.origin)

    def process_stat(self):
        self.transport.sendto(self.header_ack, self.origin)

    def process_query(self):
        self.console_output(f"Sending servers to {self.origin[0]}:{self.origin[1]}")
        servers = self.fetch_servers()
        self.transport.sendto(servers, self.origin)

    def datagram_received(self, data, address):
        self.origin = address

        message = data.split(b'\n')
        if message[0].startswith(self.header_stat):
            self.process_stat()
        elif message[0].startswith(self.header):
            command = message[0][4:]
            if command.startswith(b"heartbeat"):
                self.process_heartbeat('q2')
            elif command.startswith(b"shutdown"):
                self.process_shutdown()
            elif command.startswith(b"ping"):
                self.process_ping()
            else:
                self.console_output(f"Unknown command: {command}")
        elif message[0].startswith(b"query"):
            self.process_query()
        else:
            self.console_output(f"Unable to process message")

        try:
            session.commit()
        except:
            session.rollback()


if __name__ == '__main__':
    """
    asyncio magic
    """
    engine = create_db_conn()
    session = create_db_session(engine)
    loop = asyncio.get_event_loop()
    MasterServer.console_output(f"Starting master server")
    listen = loop.create_datagram_endpoint(MasterServer,
                                           local_addr=('0.0.0.0', 27900))
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    MasterServer.console_output(f"Shutting down master server")
    session.close()
    transport.close()
    loop.close()
