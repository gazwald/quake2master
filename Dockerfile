FROM centos:latest
RUN yum install -y centos-release-scl-rh.noarch centos-release-scl.noarch gcc geoip-devel
RUN yum install -y rh-python36-python rh-python36-python-pip rh-python36-python-virtualenv rh-python36-scldevel
RUN mkdir -p /opt/master
ADD . /opt/master/
RUN /opt/rh/rh-python36/root/usr/bin/pip3.6 install -r /opt/master/requirements.txt
CMD [ "scl", "enable", "rh-python36", "/opt/master/app.py" ]
