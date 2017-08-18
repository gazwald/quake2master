#!/usr/bin/env python3
import asyncio
import ipaddress
import struct

from schema import Game, Version, Mapname, Gamename, Server
from schema.functions import get_or_create

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class MasterServer:
    header = b'\xff\xff\xff\xff'
    header_ack = b''.join([header, b'ack'])
    header_servers = b''.join([header, b'servers '])

    def connection_made(self, transport):
        self.transport = transport

    def decoder(self, code):
        return code.decode('ascii')

    def update_server_in_db(self, address, data):
        s = Session()
        version = get_or_create(s, Version, name=data.get('version'))
        mapname = get_or_create(s, Mapname, name=data.get('mapname'))
        gamename = get_or_create(s, Gamename, name=data.get('gamename'))
        server = s.query(Server).filter_by(
            ip=address[0],
            port=address[1]
        ).first()
        if server:
            print("Updating DB")
            server.hostname = data.get('hostname')
            server.cheats = int(data.get('cheats'))
            server.needpass = int(data.get('needpass'))
            server.deathmatch = int(data.get('deathmatch'))
            server.maxclients = int(data.get('maxclients'))
            server.maxspectators = int(data.get('maxspectators'))
            server.timelimit = int(data.get('timelimit'))
            server.fraglimit = int(data.get('fraglimit'))
            server.protocol = int(data.get('protocol'))
            server.dmflags = int(data.get('dmflags'))
            server.version = version
            server.mapname = mapname
            server.gamename = gamename
            server.game = q2game
        else:
            print("Inserting DB")
            server = Server(
                hostname=data.get('hostname'),
                ip=address[0],
                port=address[1],
                cheats=int(data.get('cheats')),
                needpass=int(data.get('needpass')),
                deathmatch=int(data.get('deathmatch')),
                maxclients=int(data.get('maxclients')),
                maxspectators=int(data.get('maxspectators')),
                timelimit=int(data.get('timelimit')),
                fraglimit=int(data.get('fraglimit')),
                protocol=int(data.get('protocol')),
                dmflags=int(data.get('dmflags')),
                version=version,
                mapname=mapname,
                gamename=gamename,
                game=q2game,
            )
            s.add(server)
        s.commit()
        s.close()

    def dictify(self):
        """
        Byte string -> Byte list -> Byte Tuple list -> Dict String
        TODO: This should really be cleaned up...
              and there's a mistake in one of the examples

        Example input:
        \\cheats\\0\\dmflags\\16\\\0
        Example output:
        [b'cheats', b'0', b'dmflags', b'16']
        """
        bytes_command = self.message[1].split(b'\\')[1:]
        """
        Example output:
        [(b'cheats', b'0'), (b'dmflags', b'16')]
        """
        zipped = zip(bytes_command[0::2], bytes_command[1::2])
        """
        Example output:
        {'cheats': '0', 'dmflags': '16'}
        """
        return dict((self.decoder(x), self.decoder(y)) for x, y in zipped)

    def process_heartbeat(self, address):
        self.update_server_in_db(address, self.dictify())

    def process_shutdown(self, address):
        """
        Is this the required behaviour?
        """
        print(f"Shutdown from {address}")
        s = Session()
        s.query(Server).filter_by(ip=address[0], port=address[1]).delete()
        s.commit()
        s.close()

    def process_ping(self, address):
        print(f"Sending ack to {address}")
        self.transport.sendto(self.header_ack, address)

    def process_query(self, destination):
        print(f"Sending servers to {destination}")
        serverstring = [self.header_servers]
        for server in s.query(Server).with_entities(Server.ip, Server.port):
            ip = int(ipaddress.IPv4Address(server[0]))
            address = struct.pack('!LH', int(ip), server[1])
            serverstring.append(address)

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
    engine = create_engine('sqlite:///q2master.sqlite')
    Session = sessionmaker(bind=engine)

    """
    Grab the game type(s) once at the start
    """
    s = Session()
    q2game = get_or_create(s, Game, name='q2')
    s.close()

    """
    asyncio magic
    """
    LOCAL = ('0.0.0.0', 27900)
    loop = asyncio.get_event_loop()
    print("Starting Quake 2 master server")
    listen = loop.create_datagram_endpoint(MasterServer, local_addr=LOCAL)
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    transport.close()
    loop.close()
