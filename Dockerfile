FROM fedora:26
RUN dnf install -y python3-sqlalchemy python3-psycopg2 python3-GeoIP
RUN mkdir -p /opt/master
ADD . /opt/master/
WORKDIR /opt/master/
CMD [ "/usr/bin/python3.6", "/opt/master/app.py" ]
