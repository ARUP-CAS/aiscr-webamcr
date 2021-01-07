
### Based on: https://github.com/thinkWhere/GDAL-Docker/blob/develop/3.8-ubuntu/Dockerfile ###

#### Use latest Ubuntu
FROM ubuntu:focal

# Update base container install
RUN apt-get update
#RUN apt-get upgrade -y

ENV TZ 'GB'
RUN echo $TZ > /etc/timezone && \
    apt-get install -y tzdata && \
    rm /etc/localtime && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean

# Install GDAL dependencies
RUN apt-get install -y python3-pip libgdal-dev locales

# Ensure locales configured correctly
RUN locale-gen en_GB.UTF-8
ENV LC_ALL='en_GB.utf8'

# Set python aliases for python3
RUN echo 'alias python=python3' >> ~/.bashrc
RUN echo 'alias pip=pip3' >> ~/.bashrc

# Update C env vars so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# This will install latest version of GDAL
RUN pip3 install GDAL==3.0.4

COPY ./webclient/webclient/requirements .

RUN pip3 install -r dev.txt

RUN mkdir /code
COPY ./webclient /code
WORKDIR /code

# Uploaded images
RUN mkdir -p /vol/web/media
# Staic files for the app
RUN mkdir -p /vol/web/static

RUN adduser user
RUN passwd -d user
RUN chown -R user:user /vol
RUN chmod -R 755 /vol/web
USER user

CMD ["entrypoint.sh"]
