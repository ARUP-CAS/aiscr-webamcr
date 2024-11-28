FROM redis:7.2.5

ARG VERSION_APP

ENV VERSION=${VERSION_APP}

COPY redis.conf /home/redis/
RUN mkdir -p /scripts
COPY docker-entrypoint.sh /scripts/

COPY ./run-healthcheck_redis.sh /scripts/
RUN chmod +x /scripts/*

RUN chmod -R 755 /scripts/docker-entrypoint.sh

RUN echo "DATE:$(date +%Y%m%dT%H%M%S),VERSION:${VERSION}" > /version.txt

ENTRYPOINT ["/scripts/docker-entrypoint.sh"]