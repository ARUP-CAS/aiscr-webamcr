FROM nginxinc/nginx-unprivileged:1-alpine

ARG VERSION_APP
ARG TAG_APP

ENV VERSION=${VERSION_APP}
ENV TAG=${TAG_APP}

COPY ./default.conf /etc/nginx/conf.d/default.conf
COPY ./uwsgi_params /etx/nginx/uwsgi_params

USER root

RUN mkdir -p /vol/static
RUN chmod 755 /vol/static

RUN mkdir -p /vol/nginx/data
ADD ./custom_html /vol/nginx/data
RUN chmod 777 -R  /vol/nginx/data

RUN echo "DATE:$(date +%Y%m%dT%H%M%S),VERSION:${VERSION}" > version.txt

USER nginx
