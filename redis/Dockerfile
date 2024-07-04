FROM redis:7.2.5

COPY redis.conf /home/redis/
RUN mkdir -p /scripts
COPY docker-entrypoint.sh /scripts/

COPY ./run-healthcheck_redis.sh /scripts/
RUN chmod +x /scripts/*

RUN chmod -R 755 /scripts/docker-entrypoint.sh

ENTRYPOINT ["/scripts/docker-entrypoint.sh"]