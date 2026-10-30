FROM php:8.2-apache

# Training web target for BeaconHunt (Apache + PHP). Ships HARDENED by default;
# the range only becomes vulnerable when BeaconHunt plants artifacts at deploy.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl cron sudo iproute2 procps ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/beaconhunt/plant

# Legitimate defender/admin account (NOT a planted finding) — your blue-team
# login. SSH is not exposed on this box; use `docker compose exec web bash`
# (root) or sudo. Override with --build-arg DEFENDER_PASSWORD=...
ARG DEFENDER_USER=defender
ARG DEFENDER_PASSWORD=defender
RUN useradd -m -s /bin/bash "$DEFENDER_USER" \
    && echo "$DEFENDER_USER:$DEFENDER_PASSWORD" | chpasswd \
    && usermod -aG sudo "$DEFENDER_USER"

COPY app/ /var/www/html/
COPY plant/ /opt/beaconhunt/plant/
RUN chmod +x /opt/beaconhunt/plant/*.sh
COPY entrypoint.sh /opt/beaconhunt/entrypoint.sh
RUN chmod +x /opt/beaconhunt/entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/opt/beaconhunt/entrypoint.sh"]
