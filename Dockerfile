# Dockerfile
# ---- Stage 1: Builder ----
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.11.0 AS builder

ARG VERSION_APP
ARG TAG_APP

ENV TZ="Europe/Prague" \
    LC_ALL='cs_CZ.utf8'

RUN echo "$TZ" > /etc/timezone && \
    apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
        tzdata \
        python3-pip \
        libgdal-dev \
        locales \
        gettext \
        curl && \
    locale-gen cs_CZ.utf8 && \
    ln -sf python3 /usr/bin/python && \
    ln -sf pip3 /usr/bin/pip && \
    pip install --upgrade pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./webclient/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt --break-system-packages

COPY ./webclient /code
WORKDIR /code

# Collect static files, translations, etc.
RUN mkdir -p /vol/web/media /vol/web/static /vol/web/locale/cs/LC_MESSAGES /vol/web/locale/en/LC_MESSAGES

# ---- Stage 2: Runtime ----
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.11.0

ARG VERSION_APP
ARG TAG_APP

ENV VERSION=${VERSION_APP} \
    TAG=${TAG_APP} \
    TZ="Europe/Prague" \
    LC_ALL='cs_CZ.utf8' \
    PATH="/scripts:${PATH}"

LABEL maintainer="Archaeological Information System of the Czech Republic (AIS CR) <amcr@arup.cas.cz>" \
      org.opencontainers.image.title="aiscr-webamcr" \
      org.opencontainers.image.version="${VERSION_APP}" \
      org.opencontainers.image.description="Archaeological Map of the Czech Republic (AMCR)" \
      org.opencontainers.image.authors="Archaeological Information System of the Czech Republic (AIS CR)" \
      org.opencontainers.image.licenses="GPL-3.0-or-later" \
      org.opencontainers.image.url="https://github.com/ARUP-CAS/aiscr-webamcr" \
      org.opencontainers.image.documentation="https://aiscr-webamcr.readthedocs.io/"

RUN echo "$TZ" > /etc/timezone && \
    apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
        tzdata \
        sudo \
        cron \
        poppler-utils \
        unrar \
        jq \
        postgresql-client \
        redis-tools \
        locales \
        gettext && \
    locale-gen cs_CZ.utf8 && \
    ln -sf python3 /usr/bin/python && \
    ln -sf pip3 /usr/bin/pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy installed packages and app code from builder
COPY --from=builder /usr/local/lib/python3.*/dist-packages /usr/local/lib/python3.*/dist-packages
COPY --from=builder /code /code
WORKDIR /code

# Scripts, HTML, and permissions
COPY ./scripts /scripts
RUN chmod +x /scripts/*
COPY ./proxy/custom_html /custom_html

# Create user, directories, and fix permissions
RUN userdel ubuntu && \
    adduser --disabled-password --gecos "" user && \
    usermod -aG sudo user && \
    mkdir -p /vol/web/{media,static,locale/cs/LC_MESSAGES,locale/en/LC_MESSAGES} && \
    chown -R user:user /vol /code /custom_html && \
    chmod -R 755 /vol/web /code /custom_html

# Apply cron
RUN crontab -u user /scripts/crontab.txt

# Version info patching
RUN echo "DATE:$(date +%Y%m%dT%H%M%S),VERSION:${VERSION}" > /version.txt && \
    sed -i "s/1.0.0/${VERSION}/g" ./code/templates/base_logged_in.html && \
    sed -i "s/YYYY/$(date +%Y)/g" ./code/templates/base_logged_in.html    

# Set entrypoint and user
USER user
CMD ["entrypoint.sh"]
