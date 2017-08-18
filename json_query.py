#!/usr/bin/env python3
import json
from datetime import datetime

from schema import Server

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///q2master.sqlite')
Session = sessionmaker(bind=engine)
s = Session()

str_fmt = '%Y-%m-%d %H:%M'

serverlist = []
for server in s.query(Server).all():
    serverdict = server.__dict__
    serverdict.pop('_sa_instance_state', None)
    serverdict['first_seen'] = serverdict.get('first_seen').strftime(str_fmt)
    serverdict['last_seen'] = serverdict.get('last_seen').strftime(str_fmt)
    serverlist.append(serverdict)

print(json.dumps(serverlist, sort_keys=True, indent=4))
