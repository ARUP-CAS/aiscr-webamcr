# Dockerfile

FROM ghcr.io/osgeo/gdal:ubuntu-small-3.11.0

LABEL maintainer="Archaeological Information System of the Czech Republic (AIS CR) <amcr@arup.cas.cz>" \
      org.opencontainers.image.title="aiscr-webamcr" \
      org.opencontainers.image.version="${VERSION_APP}" \
      org.opencontainers.image.description="Archaeological Map of the Czech Republic (AMCR)" \
      org.opencontainers.image.authors="Archaeological Information System of the Czech Republic (AIS CR)" \
      org.opencontainers.image.licenses="GPL-3.0-or-later" \
      org.opencontainers.image.url="https://github.com/ARUP-CAS/aiscr-webamcr" \
      org.opencontainers.image.documentation="https://aiscr-webamcr.readthedocs.io/"

# Load arguments
ARG VERSION_APP
ARG TAG_APP

# Set environmental variables
ENV VERSION=${VERSION_APP} \
    TAG=${TAG_APP} \
    TZ="Europe/Prague" \
    LC_ALL='cs_CZ.utf8' \
    PATH="/scripts:${PATH}"

# Configure timezone and install packages
RUN echo $TZ > /etc/timezone && \
    apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install -y --no-install-recommends \
        tzdata \
        cron \
        sudo \
        python3-pip \
        libgdal-dev \
        locales \
        gettext \
        poppler-utils \
        unrar \
        jq \
        postgresql-client \
        curl \
        redis-tools && \
    locale-gen cs_CZ.utf8 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ./webclient/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt --break-system-packages && \
    rm /tmp/requirements.txt

# Set up application code
COPY ./webclient /code
COPY ./scripts /scripts
RUN chmod +x /scripts/*
COPY ./proxy/custom_html /custom_html
WORKDIR /code

# Create necessary dirs (images, static files, locales for translations)
RUN mkdir -p /vol/web/media /vol/web/static /vol/web/locale/cs/LC_MESSAGES /vol/web/locale/en/LC_MESSAGES

# Create non-root user
RUN userdel ubuntu && \
    adduser --disabled-password --gecos "" user && \
    usermod -aG sudo user && \
    chown -R user:user /vol /code /custom_html && \
    chmod -R 755 /vol/web /code /custom_html

# Apply cron
RUN crontab -u user /scripts/crontab.txt

# Update version info
RUN echo "DATE:$(date +%Y%m%dT%H%M%S),VERSION:${VERSION}" > /version.txt && \
    sed -i "s/1.0.0/${VERSION}/g" ./templates/base_logged_in.html && \
    sed -i "s/YYYY/$(date +%Y)/g" ./templates/base_logged_in.html

# Set entrypoint and user
USER user
CMD ["entrypoint.sh"]
