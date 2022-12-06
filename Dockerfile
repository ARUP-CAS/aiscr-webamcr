### Based on: https://github.com/thinkWhere/GDAL-Docker/blob/develop/3.8-ubuntu/Dockerfile ###

#### Use latest Ubuntu
FROM ubuntu:focal

# Update base container install
RUN apt-get -qq update && apt-get -qq -y install cron
RUN apt-get -y -qq install nano
RUN apt-get -y -qq install sudo
#RUN apt-get upgrade -y

ARG VERSION_APP
ARG TAG_APP

ENV VERSION=$VERSION_APP
ENV TAG=$TAG_APP
ENV DEV_CONTAINER=1

ENV TZ "Europe/Prague"
RUN echo $TZ > /etc/timezone
RUN apt-get update
RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata

# Install GDAL dependencies
RUN apt-get update
RUN apt-get install -y python3-pip libgdal-dev locales gettext


# Ensure locales configured correctly
RUN locale-gen cs_CZ.utf8
ENV LC_ALL="cs_CZ.utf8"

# Set python aliases for python3
RUN echo "alias python=python3" >> ~/.bashrc
RUN echo "alias pip=pip3" >> ~/.bashrc

# Update C env vars so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# This will install latest version of GDAL
RUN pip3 install GDAL==3.0.4

COPY ./webclient/webclient/requirements .

RUN pip3 install -r dev.txt

RUN mkdir /code
COPY ./webclient /code
COPY ./scripts /scripts
WORKDIR /code

# Uploaded images
RUN mkdir -p /vol/web/media
# Staic files for the app
RUN mkdir -p /vol/web/static

RUN mkdir -p /vol/web/locale

RUN mkdir -p /vol/web/nginx/data
ADD ./proxy/custom_html /vol/web/nginx/data

RUN echo "DATE:$(date +%Y%m%dT%H%M%S),VERSION:${VERSION}" > /version.txt
RUN adduser user
RUN passwd -d user
RUN usermod -aG sudo user
RUN chown -R user:user /vol /scripts
RUN chmod -R 755 /vol/web /scripts
RUN chmod 777 -R  /vol/web/nginx/data
RUN crontab -u user /scripts/crontab.txt
USER user

ENV PYTHONUNBUFFERED=1

CMD ["entrypoint.sh"]
