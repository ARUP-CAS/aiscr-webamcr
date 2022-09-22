FROM nginxinc/nginx-unprivileged:1-alpine

COPY ./default.conf /etc/nginx/conf.d/default.conf
COPY ./uwsgi_params /etx/nginx/uwsgi_params

USER root

RUN mkdir -p /vol/static
RUN chmod 755 /vol/static

RUN mkdir -p /vol/nginx/data
ADD ./custom_html /vol/nginx/data
RUN chmod 777 -R  /vol/nginx/data

USER nginx
