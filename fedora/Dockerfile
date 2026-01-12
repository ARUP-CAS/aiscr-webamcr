FROM fcrepo/fcrepo:6.5.1-tomcat9

RUN apt-get update
RUN apt-get install -y python3-pip
RUN apt-get update && apt-get install -y python3-requests

# Fedora na /
RUN rm -rf /usr/local/tomcat/webapps/ROOT \
    && mv /usr/local/tomcat/webapps/fcrepo /usr/local/tomcat/webapps/ROOT

RUN sed -i 's#</web-app>#  <security-role>\n    <role-name>fedoraUser</role-name>\n  </security-role>\n\n  <security-role>\n    <role-name>fedoraAdmin</role-name>\n  </security-role>\n\n</web-app>#' \
  /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml

COPY ./fedora/inputs /opt/inputs
COPY ./webclient/xml_generator/definitions/amcr.xsd /opt/inputs/amcr.xsd
COPY ./fedora/fedora-init.py /opt
COPY ./fedora/conf/fcrepo.properties /opt/fcrepo/conf/fcrepo.properties
CMD /bin/sh -c "python3 /opt/fedora-init.py & catalina.sh run"
