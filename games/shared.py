import ipaddress
import struct
import logging

import GeoIP

from sqlalchemy import and_

from database.orm import (Server,
                          Status,
                          Version,
                          Map,
                          Country,
                          Gamename)

from database.functions import get_or_create


class idTechCommon():
    """
    Parent class, intended for functions that will be common among idtech game
    """

    common = b'\xff\xff\xff\xff'
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
    def dictify(cls, data):
        """
        Input:
            b'\\cheats\\0\\deathmatch\\1\\dmflags\\16\\fraglimit\\0'
        Split the above byte-string into list of strings resulting in:
            ['cheats', '0', 'deathmatch', '1', 'dmflags', '16', 'fraglimit', '0']
        If the number of keys/values isn't equal truncate the last value
        Zip the above list of strings and then convert zip object into a dict:
            {'cheats': 0, 'deathmatch': 1, 'dmflags': 16, 'fraglimit': 0]
        For each key/value try to convert it to an int ahead of time.

        At the end of the heartbeat is the player list split by \n
        Example: <score> <ping> <player>\n

        """
        status = dict()

        if data[1:]:
            status['clients'] = len(data[2:])

        if data[0]:
            str_status = data[0].decode('ascii')
            list_status = str_status.split('\\')[1:]
            if len(list_status) % 2 != 0:
                list_status = list_status[:-1]

            zip_status = zip(list_status[0::2], list_status[1::2])

            for status_k, status_v in zip_status:
                if len(status_v) > 128:
                    status_v = status_v[:128]

                try:
                    status[status_k] = int(status_v)
                except ValueError:
                    status[status_k] = status_v

        return status

    @classmethod
    def is_q2(cls, data):
        """
        Determines if a specific request is a Quake 2 server or client
        """
        command = data[:13]
        return any(v for v in idTechCommon.headers['quake2'].values() if v.startswith(command))

    def get_server(self, address):
        """
        Helper function - returns a server based on adress:port
        """
        return self.session.query(Server)\
                           .filter_by(ip=address[0],
                                      port=address[1],
                                      game=self.game).first()

    def get_version(self, version):
        """
        Helper function - gets or creates a Version object and returns
        """
        return get_or_create(self.session,
                             Version,
                             name=version)

    def get_mapname(self, mapname):
        """
        Helper function - gets or creates a Mapname object and returns
        """
        return get_or_create(self.session,
                             Map,
                             name=mapname)

    def get_gamename(self, gamename):
        """
        Helper function - gets or creates a Gamename object and returns
        """
        return get_or_create(self.session,
                             Gamename,
                             name=gamename)

    def get_country(self, address):
        """
        Helper function - gets or creates a Country object and returns
        """
        return get_or_create(self.session,
                             Country,
                             name_short=self.gi.country_code_by_addr(address[0]),
                             name_long=self.gi.country_name_by_addr(address[0]))

    def update_status(self, server, status_dict):
        """
        Set all attributes from heartbeat such as map name, version, etc
        status_dict should be the output of dictify, which should have been
        passed the whole message split at \n
        """
        status_dict['server'] = server
        status_dict['version'] = self.get_version(status_dict.get('version'))
        status_dict['map'] = self.get_mapname(status_dict.get('mapname'))
        status_dict['gamename'] = self.get_gamename(status_dict.get('gamename'))
        try:
            del status_dict['gamedate']
        except KeyError:
            pass
        try:
            del status_dict['mapname']
        except KeyError:
            pass

        status = self.session.query(Status)\
                             .join(Status.server)\
                             .filter(Status.server == server).first()

        if status:
            for status_k, status_v in status_dict.items():
                setattr(status, status_k, status_v)
        else:
            status = Status(**status_dict)

        self.session.add(status)


class Master(idTechCommon):
    """
    Parent class, intended for functions that will be common among idtech masters
    """
    def __init__(self):
        super().__init__()
        self.gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

    def process_heartbeat(self, address, message):
        """
        Processes a server heartbeat
        """
        logging.info(f"Heartbeat from {address[0]}:{address[1]}")
        server = self.get_server(address)
        if not server:
            server = Server(
                active=True,
                ip=address[0],
                port=address[1],
                game=self.game,
                country=self.get_country(address)
            )
        else:
            server.active = True

        self.session.add(server)

        self.update_status(server, self.dictify(message))

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

        return idTechCommon.headers[self.game.name]['ack']

    def process_query(self, address):
        """
        Returns a list of servers (as bytes)
        For consumption by clients, eg: qstat
        """
        logging.info(f"Sending servers to {address[0]}:{address[1]}")
        if self.game.name == 'quake2':
            serverstring = [idTechCommon.headers[self.game.name]['servers']]
        else:
            serverstring = []

        for server in self.session.query(Server)\
                                  .filter(and_(Server.active,
                                               Server.game == self.game))\
                                  .with_entities(Server.ip,
                                                 Server.port).all():
            serverstring.append(self.bytepack(server))

        return b''.join(serverstring)
