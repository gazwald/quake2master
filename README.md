# Quake 2 Master

This project originally started as a desire to aggregate the server lists for the various Quake 2 master servers.

However most Quake 2 master servers these days appear to be dead and of the one that isn't [q2servers](http://q2servers.com/) it does not support b'query\n\0'.

Goals for this project:
* Write servers to DB backend - probably using PostgreSQL
* Rest API for DB backend - probably using Flask
* Front end for rest API - probably using VueJS
* Unit tests for all!

## Should I use this as a production Quake 2 master server?
No. It's barely tested at the time of writing.

## Testing
Querying the server has only been tested using [QStat](https://github.com/multiplay/qstat) and manually querying the server with Python.

Quake 2 server code used: [Yamagi Quake II](https://github.com/yquake2/yquake2) release 7.01 

Built and tested using Python 3.6

## Specs
Specs were cobbled together using the [QStat](https://github.com/multiplay/qstat) source, [Quake 2](https://github.com/id-Software/Quake-2) source and tcpdump.
