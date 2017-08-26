#!/usr/bin/env python3
import asyncio
import ipaddress
import struct
import configparser
from datetime import datetime

from schema import Game, Server
from schema.functions import get_or_create

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class MasterServer:
    header = b'\xff\xff\xff\xff'
    header_ack = b''.join([header, b'ack'])
    header_servers = b''.join([header, b'servers '])

    @staticmethod
    def console_output(message):
        print(f"{datetime.utcnow().isoformat()}: {message}")

    def connection_made(self, transport):
        self.transport = transport

    def process_heartbeat(self, address):
        self.console_output(f"Heartbeat from {address[0]}:{address[1]}")
        s = Session()
        game = get_or_create(s, Game, name='q2')
        server = s.query(Server).filter_by(
            ip=address[0],
            port=address[1]
        ).first()
        if not server:
            server = Server(
                active=True,
                ip=address[0],
                port=address[1],
                game=game,
            )
            s.add(server)
            s.commit()
        s.close()

    def process_shutdown(self, address):
        self.console_output(f"Shutdown from {address[0]}:{address[1]}")
        s = Session()
        server = s.query(Server).filter_by(ip=address[0],
                                           port=address[1]).first()
        if server:
            server.active = False
            s.commit()
        s.close()

    def process_ping(self, address):
        self.console_output(f"Sending ack to {address[0]}:{address[1]}")
        s = Session()
        server = s.query(Server).filter_by(ip=address[0],
                                           port=address[1]).first()
        if server:
            server.active = True
            s.commit()
        s.close()
        self.transport.sendto(self.header_ack, address)

    def process_query(self, destination):
        self.console_output(f"Sending servers to {destination[0]}:{destination[1]}")
        serverstring = [self.header_servers]
        s = Session()
        for server in s.query(Server).filter(Server.active)\
                                     .with_entities(Server.ip, Server.port):
            ip = int(ipaddress.IPv4Address(server[0]))
            address = struct.pack('!LH', int(ip), server[1])
            serverstring.append(address)

        s.close()
        self.transport.sendto(b''.join(serverstring), destination)

    def datagram_received(self, data, address):
        self.message = data.split(b'\n')
        if self.message[0].startswith(self.header):
            command = self.message[0][4:]
            if command.startswith(b"heartbeat"):
                self.process_heartbeat(address)
            elif command.startswith(b"shutdown"):
                self.process_shutdown(address)
            elif command.startswith(b"ping"):
                self.process_ping(address)
            else:
                print(f"Unknown command: {command}")
        elif self.message[0].startswith(b"query"):
            self.process_query(address)
        else:
            print(f"Unknown command: {command}")


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    dbstring = 'postgresql://{username}:{password}@{host}:{port}/{database}'
    engine = create_engine(dbstring.format(username=config['database']['username'],
                                           password=config['database']['password'],
                                           host=config['database']['host'],
                                           port=config['database']['port'],
                                           database=config['database']['database']))
    Session = sessionmaker(bind=engine)

    """
    asyncio magic
    """
    LOCAL = ('0.0.0.0', 27900)
    loop = asyncio.get_event_loop()
    MasterServer.console_output(f"Starting Quake 2 master server on {LOCAL[0]}:{LOCAL[1]}")
    listen = loop.create_datagram_endpoint(MasterServer, local_addr=LOCAL)
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    MasterServer.console_output(f"Shutting down Quake 2 master server")
    transport.close()
    loop.close()
