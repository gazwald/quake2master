# Quake 2 master server

This project originally started as a desire to aggregate the server lists for the various Quake 2 master servers.

However most Quake 2 master servers these days appear to be dead and of the one that isn't dead ([q2servers.com](http://q2servers.com/)) it doesn't appear to support b'query\n\0'.

Core goals for this project:
* Write servers to PostgreSQL backend for state management - Done
* Rest API for PostgreSQL backend;
  * Flask for testing/PoC - In Progress
  * AWS Lambda/API Gateway for production
* Front end for rest API - probably using VueJS - In Progress
* Deployment/Load balancing through Docker - In Progress

Stretch goals:
* Unit/Integration tests
* Automated CI/CD pipeline
* Support for Quake 1/W and Quake 3

All of the above should be tracked in issues/GitHub projects soon.

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
* [This implimentation](q2.rlogin.dk/news/2016/Setting-up-your-own-Quake-2-Master-server)
* And good ol' tcpdump.
