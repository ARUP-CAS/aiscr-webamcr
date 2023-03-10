FROM redis:7

COPY redis.conf /home/redis/
RUN mkdir -p /scripts
COPY docker-entrypoint.sh /scripts/

RUN chmod -R 755 /scripts/docker-entrypoint.sh

ENTRYPOINT ["/scripts/docker-entrypoint.sh"]