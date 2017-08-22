#!/usr/bin/env python3
from sqlalchemy import (Column,
                        ForeignKey,
                        SmallInteger,
                        Integer,
                        String,
                        Boolean,
                        DateTime)
from sqlalchemy.dialects import postgresql
from sqlalchemy import (create_engine,
                        func)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Version(Base):
    __tablename__ = 'version'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), index=True, unique=True)


class Game(Base):
    __tablename__ = 'game'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), index=True, unique=True)


class Map(Base):
    __tablename__ = 'map'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), index=True, unique=True)


class Country(Base):
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True)
    name_short = Column(String(2), index=True, unique=True)
    name_long = Column(String(50), index=True, unique=True)


class Server(Base):
    __tablename__ = 'server'
    id = Column(Integer, primary_key=True)
    ip = Column(postgresql.INET, index=True, nullable=False)
    port = Column(SmallInteger, index=True, nullable=False)
    active = Column(Boolean)
    first_seen = Column(DateTime,
                        server_default=func.now())
    last_seen = Column(DateTime,
                       server_default=func.now(),
                       onupdate=func.now())

    country_id = Column(Integer, ForeignKey('country.id'))
    country = relationship(Country, lazy='joined')

    game_id = Column(Integer, ForeignKey('game.id'))
    game = relationship(Game, lazy='joined')


class Status(Base):
    __tablename__ = 'status'
    id = Column(Integer, primary_key=True)
    hostname = Column(String(250))
    cheats = Column(SmallInteger)
    needpass = Column(SmallInteger)
    deathmatch = Column(SmallInteger)
    clients = Column(SmallInteger)
    maxclients = Column(SmallInteger)
    spectators = Column(SmallInteger)
    maxspectators = Column(SmallInteger)
    timelimit = Column(SmallInteger)
    fraglimit = Column(SmallInteger)
    protocol = Column(SmallInteger)
    dmflags = Column(Integer)
    uptime = Column(String(50))

    server_id = Column(Integer, ForeignKey('server.id'))
    server = relationship(Server, lazy='joined')

    map_id = Column(Integer, ForeignKey('map.id'))
    map = relationship(Map, lazy='joined')

    version_id = Column(Integer, ForeignKey('version.id'))
    version = relationship(Version, lazy='joined')


class Player(Base):
    __tablename__ = 'player'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    score = Column(SmallInteger)
    ping = Column(SmallInteger)

    server_id = Column(Integer, ForeignKey('server.id'))
    server = relationship(Server, lazy='joined')


"""
TODO: Move DB creation into 'functions.py'
"""
connectionstr = 'postgresql://q2master:password@192.168.124.86:5432/q2master'
engine = create_engine(connectionstr)
Base.metadata.create_all(engine)
