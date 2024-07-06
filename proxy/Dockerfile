FROM nginxinc/nginx-unprivileged:1.26.1-alpine3.19

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

COPY ./run-healthcheck_proxy.sh /scripts/
RUN chmod +x /scripts/*

RUN echo "DATE:$(date +%Y%m%dT%H%M%S),VERSION:${VERSION}" > /version.txt

USER nginx
