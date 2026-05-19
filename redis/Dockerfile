# Dockerfile for Redis

FROM redis:8.6.3

ARG VERSION_APP
ARG TAG_APP

ENV VERSION=${VERSION_APP}
ENV TAG=${TAG_APP}

COPY redis.conf /home/redis/

# Combine script operations
COPY docker-entrypoint.sh ./run-healthcheck_redis.sh /scripts/
RUN chmod +x /scripts/* && \
    chmod -R 755 /scripts/docker-entrypoint.sh

# Write version info (NOTE: this will be static at build time)
RUN echo "DATE:$(date +%Y%m%dT%H%M%S),VERSION:${VERSION}" > /version.txt

ENTRYPOINT ["/scripts/docker-entrypoint.sh"]
