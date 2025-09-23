# Dockerfile for Nginx Proxy

FROM nginxinc/nginx-unprivileged:1.27.3-alpine3.20

ARG VERSION_APP
ARG TAG_APP

ENV VERSION=${VERSION_APP}
ENV TAG=${TAG_APP}

COPY ./default.conf /etc/nginx/conf.d/default.conf
COPY ./uwsgi_params /etc/nginx/uwsgi_params

USER root

COPY ./run-healthcheck_proxy.sh /scripts/

RUN mkdir -p /vol/static /vol/nginx/data && \
    chmod 755 /vol/static && \
    chmod 777 -R /vol/nginx/data && \
    chmod +x /scripts/*

RUN sh -c 'echo "DATE:$(date +%Y%m%dT%H%M%S),VERSION=${VERSION}" > /version.txt'

USER nginx
