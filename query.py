#!/usr/bin/env python3
import socket
import configparser
import re

from schema import Server, Status, Map, Version, Gamename, Player
from schema.functions import get_or_create

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker


config = configparser.ConfigParser()
config.read('config.ini')
dbstring = 'postgresql://{username}:{password}@{host}:{port}/{database}'
engine = create_engine(dbstring.format(username=config['database']['username'],
                                       password=config['database']['password'],
                                       host=config['database']['host'],
                                       port=config['database']['port'],
                                       database=config['database']['database']))
Session = sessionmaker(bind=engine)
db = Session()

str_fmt = '%Y-%m-%d %H:%M'
player_regex = re.compile('(?P<score>\d+) (?P<ping>\d+) (?P<name>".+")', flags=re.ASCII)

q2header = b'\xff\xff\xff\xff'
q2servers = q2header + b'status 23\x0a'
q2print = q2header + b'print'


def dictify(message):
    """
    Input:
        b'\\cheats\\0\\deathmatch\\1\\dmflags\\16\\fraglimit\\0'
    Split the above byte-string into list of byte strings resulting in:
        [b'cheats', b'0', b'deathmatch', b'1', b'dmflags', b'16', b'fraglimit', b'0']
    Zip the above list of byte strings and then convert zip object into a dict:
        {'cheats': '0', 'deathmatch': '1', 'dmflags': '16', 'fraglimit': '0']
    Dict conversion also decodes from Bytes to ASCII
    TODO: Look for improvements here
    """
    bytes_command = message.split(b'\\')[1:]
    zipped = zip(bytes_command[0::2], bytes_command[1::2])
    status = dict((x.decode('ascii'), y.decode('ascii')) for x, y in zipped)
    return status


def update_status(server, serverstatus):
    version = get_or_create(db, Version, name=serverstatus.get('version'))
    mapname = get_or_create(db, Map, name=serverstatus.get('mapname'))
    gamename = get_or_create(db, Gamename, name=serverstatus.get('gamename'))
    clients = db.query(Player).join(Player.server).filter(Player.server == server).count()
    print(clients)
    status = db.query(Status).join(Status.server).filter(Status.server == server).first()
    if status:
        status.hostname = serverstatus.get('hostname')
        status.cheats = int(serverstatus.get('cheats'))
        status.needpass = int(serverstatus.get('needpass'))
        status.deathmatch = int(serverstatus.get('deathmatch'))
        status.clients = clients
        status.maxclients = int(serverstatus.get('maxclients'))
        status.maxspectators = int(serverstatus.get('maxspectators'))
        status.timelimit = int(serverstatus.get('timelimit'))
        status.fraglimit = int(serverstatus.get('fraglimit'))
        status.protocol = int(serverstatus.get('protocol'))
        status.dmflags = int(serverstatus.get('dmflags'))
        status.version = version
        status.map = mapname
        status.gamename = gamename
    else:
        status = Status(
            hostname=serverstatus.get('hostname'),
            cheats=int(serverstatus.get('cheats')),
            needpass=int(serverstatus.get('needpass')),
            deathmatch=int(serverstatus.get('deathmatch')),
            clients=clients,
            maxclients=int(serverstatus.get('maxclients')),
            maxspectators=int(serverstatus.get('maxspectators')),
            timelimit=int(serverstatus.get('timelimit')),
            fraglimit=int(serverstatus.get('fraglimit')),
            protocol=int(serverstatus.get('protocol')),
            dmflags=int(serverstatus.get('dmflags')),
            server=server,
            version=version,
            map=mapname,
            gamename=gamename,
        )
        db.add(status)
    db.commit()


def update_players(server, players):
    """
    TODO: Remove players that no longer exist on the server
    TODO: Deal with duplicates
    """
    for playerstate in players:
        playerstate = playerstate.decode('ascii')
        if playerstate:
            playerstate = re.match(player_regex, playerstate)
            player = db.query(Player).join(Player.server)\
                                     .filter(and_(Player.server == server,
                                                  Player.name == playerstate.group('name'))).first()
            if player:
                player.score = int(playerstate.group('score'))
                player.ping = int(playerstate.group('ping'))
            else:
                player = Player(
                    score=int(playerstate.group('score')),
                    ping=int(playerstate.group('ping')),
                    name=playerstate.group('name'),
                    server=server
                )
                db.add(player)
            db.commit()


def process_server_info(server, message):
    if message[0].startswith(q2print):
        status = message[1]
        players = message[2:]
        if players:
            update_players(server, players)
        if status:
            update_status(server, dictify(status))


with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(5)
    for server in db.query(Server).filter(Server.active):
        try:
            print(f"Connecting to {server}...")
            s.connect((server.ip, server.port))
        except socket.error as msg:
            print(f"Connection error: {msg}")
        else:
            s.send(q2servers)
            data = s.recv(1024)
            message = data.split(b'\n')
            process_server_info(server, message)
