# Quake 2 master server

This project originally started as a desire to aggregate the server lists for the various Quake 2 master servers.

However most Quake 2 master servers these days appear to be dead and of the one that isn't dead ([q2servers.com](http://q2servers.com/)) it doesn't appear to support b'query\n\0'.

So what started as an initial curiosity has turned into a rather large project.

## Parts
### Master
[Master](https://github.com/gazwald/quake2master) - Contains the core part of the master server. Accepts connections from Quake 2 servers and queries from clients.

### Query Engine
[Query Engine](https://github.com/gazwald/quake2master-query) - Intended to be run periodically to query the list of servers and gather details about individual Quake 2 servers and the players on them

### Database
[Database](https://github.com/gazwald/quake2master-db) - Database components that are shared by all of the above as a submodule

### Middleware
TODO. AWS Lambda functions for the frontend will go here.

### Frontend
[Frontend](https://github.com/gazwald/quake2master-frontend) - VueJS Middleware consumer will go here.

## Cloning
git clone ...

git submodule update --init --recursive

## Should I use this as a production Quake 2 master server?
Although I still think the answer is 'no', if you want to use it in production go ahead.

## Testing
Querying the server has only been tested using [QStat](https://github.com/multiplay/qstat) and manually querying the server with Python.

Quake 2 server code used: [Yamagi Quake II](https://github.com/yquake2/yquake2) release 7.01+

Built and tested using Python 3.6

## Specs
Specs were cobbled together using the following:
* [QStat](https://github.com/multiplay/qstat)
* [Quake 2](https://github.com/id-Software/Quake-2)
* [This implimentation](http://q2.rlogin.dk/news/2016/Setting-up-your-own-Quake-2-Master-server)
* And good ol' tcpdump.
