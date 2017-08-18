#!/usr/bin/env python3
from sqlalchemy import (Column,
                        ForeignKey,
                        SmallInteger,
                        Integer,
                        String,
                        Boolean,
                        Date)
from sqlalchemy import (create_engine,
                        func)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Version(Base):
    __tablename__ = 'version'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


class Mapname(Base):
    __tablename__ = 'mapname'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


class Game(Base):
    __tablename__ = 'game'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


class Gamename(Base):
    __tablename__ = 'gamename'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)


class Server(Base):
    __tablename__ = 'server'
    id = Column(Integer, primary_key=True)
    hostname = Column(String(250), nullable=False)
    ip = Column(String(15), nullable=False)
    port = Column(SmallInteger, nullable=False)
    cheats = Column(SmallInteger, nullable=False)
    needpass = Column(SmallInteger, nullable=False)
    deathmatch = Column(Boolean, nullable=False)
    maxclients = Column(SmallInteger, nullable=False)
    maxspectators = Column(SmallInteger, nullable=False)
    timelimit = Column(SmallInteger, nullable=False)
    fraglimit = Column(SmallInteger, nullable=False)
    protocol = Column(SmallInteger, nullable=False)
    dmflags = Column(SmallInteger, nullable=False)
    first_seen = Column(Date, server_default=func.now())
    last_seen = Column(Date, server_default=func.now(), onupdate=func.now())
    mapname_id = Column(Integer, ForeignKey('mapname.id'))
    mapname = relationship(Mapname)
    gamename_id = Column(Integer, ForeignKey('gamename.id'))
    gamename = relationship(Gamename)
    version_id = Column(Integer, ForeignKey('version.id'))
    version = relationship(Version)
    game_id = Column(Integer, ForeignKey('game.id'))
    game = relationship(Game)


# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine('sqlite:///q2master.db')

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)
