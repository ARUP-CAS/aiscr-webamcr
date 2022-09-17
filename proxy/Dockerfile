FROM nginxinc/nginx-unprivileged:1-alpine

COPY ./default.conf /etc/nginx/conf.d/default.conf
COPY ./uwsgi_params /etx/nginx/uwsgi_params
COPY ./custom_html/custom_50x.html /usr/share/nginx/html
COPY ./custom_html/custom_50x_copy.html /usr/share/nginx/html/oznameni/custom_50x_copy.html
COPY ./custom_html/custom_50x_copy.html /usr/share/nginx/html/custom_50x_copy.html

USER root

RUN mkdir -p /vol/static
RUN chmod 755 /vol/static

USER nginx
