FROM ghcr.io/osgeo/gdal:ubuntu-small-3.12.3 AS python-builder

ENV DEBIAN_FRONTEND=noninteractive \
    TZ="Europe/Prague"

RUN echo $TZ > /etc/timezone && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-pip \
        python3-dev \
        build-essential \
        gcc \
        libpq-dev \
        tzdata \
        cron \
        sudo \
        libgdal-dev \
        locales \
        gettext \
        poppler-utils \
        unrar \
        jq \
        postgresql-client \
        curl \
        libmagic1 \
        redis-tools \
        nodejs \
        npm && \
    locale-gen cs_CZ.utf8 && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY ./webclient/requirements.txt /tmp/requirements.txt
COPY ./package*.json /node_modules_build/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 wheel --wheel-dir /wheels -r /tmp/requirements.txt

RUN --mount=type=cache,target=/root/.npm \
    cd /node_modules_build && npm ci

FROM python-builder AS app-builder

COPY --from=python-builder /wheels /wheels
RUN pip3 install --no-cache-dir --no-index --find-links=/wheels /wheels/* --break-system-packages --ignore-installed && \
    rm -rf /wheels ~/.cache/pip

COPY ./webclient /code
WORKDIR /code

RUN python3 -m compileall -b /code

FROM ghcr.io/osgeo/gdal:ubuntu-small-3.12.3 AS runtime

ARG VERSION_APP
ARG TAG_APP

LABEL maintainer="Archaeological Information System of the Czech Republic (AIS CR) <amcr@arup.cas.cz>" \
      org.opencontainers.image.title="aiscr-webamcr" \
      org.opencontainers.image.version="${VERSION_APP}" \
      org.opencontainers.image.description="Archaeological Map of the Czech Republic (AMCR)" \
      org.opencontainers.image.authors="Archaeological Information System of the Czech Republic (AIS CR)" \
      org.opencontainers.image.licenses="GPL-3.0-or-later" \
      org.opencontainers.image.url="https://github.com/ARUP-CAS/aiscr-webamcr" \
      org.opencontainers.image.documentation="https://aiscr-webamcr.readthedocs.io/"

ENV VERSION=${VERSION_APP} \
    TAG=${TAG_APP} \
    TZ="Europe/Prague" \
    LC_ALL='cs_CZ.utf8' \
    PATH="/scripts:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN echo $TZ > /etc/timezone && \
    apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
        tzdata \
        cron \
        sudo \
        python3 \
        python3-pip \
        libgdal-dev \
        locales \
        gettext \
        poppler-utils \
        unrar \
        jq \
        postgresql-client \
        curl \
        libmagic1 \
        redis-tools && \
    locale-gen cs_CZ.utf8 && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=python-builder /wheels /wheels
RUN pip3 install --no-cache-dir --no-index --find-links=/wheels /wheels/* --break-system-packages --ignore-installed && \
    rm -rf /wheels ~/.cache/pip

COPY --from=app-builder /code /code
COPY --from=python-builder /node_modules_build/node_modules /node_modules

RUN mkdir -p /vol/web/media /vol/web/static /vol/web/locale/cs/LC_MESSAGES /vol/web/locale/en/LC_MESSAGES && \
    userdel ubuntu && \
    adduser --disabled-password --gecos "" user && \
    passwd -d user && \
    usermod -aG sudo user

WORKDIR /code
COPY --chown=user:user ./scripts /scripts
COPY --chown=user:user ./proxy/custom_html /custom_html

RUN chmod +x /scripts/* && \
    chmod -R 755 /vol/web /code /custom_html && \
    chown -R user:user /vol /code /custom_html && \
    crontab -u user /scripts/crontab.txt && \
    echo "DATE:$(date +%Y%m%dT%H%M%S),VERSION:${VERSION}" > /version.txt && \
    sed -i "s/1.0.0/${VERSION}/g" ./templates/base_logged_in.html && \
    sed -i "s/YYYY/$(date +%Y)/g" ./templates/base_logged_in.html

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

USER user
CMD ["entrypoint.sh"]
