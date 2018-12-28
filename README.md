# Overview

[![Build status](https://badge.buildkite.com/c394aa3ab564cf49587c4e675b77310b1e2d48627d96f3fc5c.svg)](https://buildkite.com/quake-services/quake-master)

This project originally started as a desire to scrape active Quake 2 master servers and provide both a REST API and a backwards compatible interface for programs like qstat.

The only two remaining Quake 2 master servers that I am aware of;

- q2servers.com
- q2.rlogin.dk/master

Initially in my search for Quake 2 master servers I missed the second (rlogin.dk) server and both of the above support a binary query format which I didn't realise at the time of this projects inception.

During development and the discovery of the above this project has morphed into a few different things for my own personal amusement.

## Goals

I'd like to provide a Quake 2 library written in Python for the following functionality:

- Creating Quake 2 master servers
- Creating simple Quake 2 clients for querying servers
- Allow and test for protocol 35, 36, and 37
- Synthetically testing Quake 2 masters, servers, and clients.
- Store GeoIP data
- Unit/Integration/Functional tests for everything
- Documentation

Stretch goals:
- Application load balancer
- Expand to QuakeWorld and Quake 3 libraries/support

## But why?

A combination of nostalgia and the potential that this could turn into a project that utilises the full stack from sockets up to a web frontend and a full CI/CD pipeline.

Nostalgia started this project but DevOps will finish it.

# Deployment

Minimum requirements:
- Python 3.6
- PostgreSQL 9.6

Recommended requirements:
- Docker

All deployment testing for this project has been done on CentOS 7.2+ or Fedora 25+

## Master server

TODO

The master server in its current implementation can only be load balanced via NGINX (using proxy_bind) or LVS (Direct Routing). This is due to the way socket communication is handled - all other forms of load balancing tested resulted in the load balancers IP address being stored instead of the origin address.

It's unknown at this point if this limitation is with the Python socket handler or with my understanding of them; most likely the latter and assuming that it is the latter this should be considered a bug.

Due to the simplicity of setup/configuration NGINX is recommended at the moment.

## Query Engine

TODO

See [quake2master-query](https://github.com/gazwald/quake2master-query)

## Frontend and Backend

### Frontend

TODO

Utilises VueJS/Vuetify - needs reworking to take advantage of WebPack

[quake2master-frontend](https://github.com/gazwald/quake2master-frontend)

### Backend

TODO

Simple Flask app that returns JSON for the frontend to consume

[quake2master-rest](https://github.com/gazwald/quake2master-rest)

# Contributing

This is my first reasonably large personal project that doesn't heavily leverage an existing framework so if you find a bug or have a suggestion your input will be welcome.

This license for this project is GNU General Public License v3.0

Tab = 4 spaces

# Documentation

A lot of this was made considerably easier by the folks before me who documentation and researched the aspects of the Quake 2 networking stack. Below is a list of URLs I found useful while undertaking this project:

- [Quake 2 source code](https://github.com/id-Software/Quake-2)
- [Quake 2 source code review](http://fabiensanglard.net/quake2/index.php)
- [Quake Stat](https://github.com/multiplay/qstat)
- [Q2Pro source (protocol 36)](https://github.com/AndreyNazarov/q2pro)
- [R1Q2 (protocol 37) documentation](https://r-1.ch/r1q2-protocol.txt)
- [R1Q2 source (protocol 37)](https://github.com/tastyspleen/r1q2-archive)

