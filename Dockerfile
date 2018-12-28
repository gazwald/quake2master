FROM centos:latest
RUN mkdir -p /opt/master
ADD . /opt/master/
WORKDIR /opt/master/
RUN scripts/bootstrap
CMD [ "scl", "enable", "rh-python36", "app.py" ]
