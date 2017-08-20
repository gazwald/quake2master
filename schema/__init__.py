#!/usr/bin/env python3
from sqlalchemy import (Column,
                        ForeignKey,
                        SmallInteger,
                        Integer,
                        String,
                        Boolean,
                        DateTime)
from sqlalchemy import (create_engine,
                        func)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Version(Base):
    __tablename__ = 'version'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    def __repr__(self):
        return self.name


class Mapname(Base):
    __tablename__ = 'mapname'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    def __repr__(self):
        return self.name


class Game(Base):
    __tablename__ = 'game'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    def __repr__(self):
        return self.name


class Gamename(Base):
    __tablename__ = 'gamename'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    def __repr__(self):
        return self.name


class Server(Base):
    __tablename__ = 'server'
    id = Column(Integer, primary_key=True)
    hostname = Column(String(250), nullable=False)
    ip = Column(String(15), nullable=False)
    port = Column(SmallInteger, nullable=False)
    cheats = Column(SmallInteger, nullable=False)
    needpass = Column(SmallInteger, nullable=False)
    deathmatch = Column(SmallInteger, nullable=False)
    maxclients = Column(SmallInteger, nullable=False)
    maxspectators = Column(SmallInteger, nullable=False)
    timelimit = Column(SmallInteger, nullable=False)
    fraglimit = Column(SmallInteger, nullable=False)
    protocol = Column(SmallInteger, nullable=False)
    dmflags = Column(SmallInteger, nullable=False)
    first_seen = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime,
                       server_default=func.now(),
                       onupdate=func.now())
    active = Column(Boolean)
    mapname_id = Column(Integer, ForeignKey('mapname.id'))
    mapname = relationship(Mapname, lazy='joined')
    gamename_id = Column(Integer, ForeignKey('gamename.id'))
    gamename = relationship(Gamename, lazy='joined')
    version_id = Column(Integer, ForeignKey('version.id'))
    version = relationship(Version, lazy='joined')
    game_id = Column(Integer, ForeignKey('game.id'))
    game = relationship(Game, lazy='joined')


"""
TODO: Move DB creation into 'functions.py'
"""
engine = create_engine('sqlite:///q2master.sqlite')
Base.metadata.create_all(engine)
