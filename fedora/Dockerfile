FROM fcrepo/fcrepo:6.4.0

RUN apt-get update
RUN apt-get install -y python3-pip
RUN pip install requests

COPY ./fedora/inputs /opt/inputs
COPY ./webclient/xml_generator/definitions/amcr.xsd /opt/inputs/amcr.xsd
COPY ./fedora/fedora-init.py /opt
COPY ./fedora/conf/server.xml /usr/local/tomcat/conf/server.xml
COPY ./fedora/conf/fcrepo.properties /opt/fcrepo/conf/fcrepo.properties
CMD /bin/sh -c "python3 /opt/fedora-init.py & catalina.sh run"
