#!/usr/bin/env python3
import socket
import configparser
import re
from datetime import datetime

from schema import (Server,
                    Status,
                    Map,
                    Version,
                    Gamename,
                    Player,
                    State)
from schema.functions import get_or_create

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


q2header = b'\xff\xff\xff\xff'
q2servers = q2header + b'status 23\x0a'
q2print = q2header + b'print'


def dictify(message):
    """
    Input:
        b'\\cheats\\0\\deathmatch\\1\\dmflags\\16\\fraglimit\\0'
    Split the above byte-string into list of strings resulting in:
        ['cheats', '0', 'deathmatch', '1', 'dmflags', '16', 'fraglimit', '0']
    Zip the above list of byte strings and then convert zip object into a dict:
        {'cheats': '0', 'deathmatch': '1', 'dmflags': '16', 'fraglimit': '0']
    TODO: Look for improvements here
    """
    strmessage = message.decode('ascii')
    strstatus = strmessage.split('\\')[1:]
    zipped = zip(strstatus[0::2], strstatus[1::2])
    status = dict((x, y) for x, y in zipped)
    return status


def update_status(server, serverstatus):
    """
    TODO: Clean this up
    """
    version = get_or_create(db, Version, name=serverstatus.get('version'))
    mapname = get_or_create(db, Map, name=serverstatus.get('mapname'))
    gamename = get_or_create(db, Gamename, name=serverstatus.get('gamename'))
    clients = db.query(Player).join(Player.server).filter(Player.server == server).count()
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
    player_regex = re.compile('(?P<score>-?\d+) (?P<ping>\d+) (?P<name>".+")', flags=re.ASCII)
    player_list = []
    db.query(Player).filter(Player.server == server).delete()
    db.commit()
    for playerstate in players:
        if playerstate:
            playerstate = playerstate.decode('ascii')
            playerstate = re.match(player_regex, playerstate)
            playerlist.append(Player(
                score=int(playerstate.group('score')),
                ping=int(playerstate.group('ping')),
                name=playerstate.group('name'),
                server=server
            ))
    db.add_all(playerlist)
    db.commit()


def process_server_info(server, message):
    if message[0].startswith(q2print):
        status = message[1]
        players = message[2:]
        if players:
            update_players(server, players)
        if status:
            update_status(server, dictify(status))


def query_servers():
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
    db = Session()
    state = db.query(State).first()
    if not state.running:
        state.running = True
        state.started = datetime.now()
        db.commit()

        query_servers()

        state.ended = datetime.now()
        state.running = False
        db.commit()

    db.close()
