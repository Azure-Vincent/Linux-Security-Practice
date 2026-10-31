FROM debian:12-slim

# Training DNS target for BeaconHunt (BIND9). Ships HARDENED (no recursion, no
# zone transfers); BeaconHunt plants the loose config / rogue records at deploy.
# Detection is file-based, so the range works even if named is slow to start.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        bind9 bind9utils dnsutils cron curl sudo procps iproute2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/beaconhunt/plant

# Legitimate defender/admin account (NOT a planted finding). No SSH here; use
# `docker compose exec dns bash` (root) or sudo.
ARG DEFENDER_USER=defender
ARG DEFENDER_PASSWORD=defender
RUN useradd -m -s /bin/bash "$DEFENDER_USER" \
    && echo "$DEFENDER_USER:$DEFENDER_PASSWORD" | chpasswd \
    && usermod -aG sudo "$DEFENDER_USER"

COPY named.conf.options /etc/bind/named.conf.options
COPY named.conf.local   /etc/bind/named.conf.local
COPY db.acme.local      /etc/bind/db.acme.local
COPY plant/ /opt/beaconhunt/plant/
RUN chmod +x /opt/beaconhunt/plant/*.sh
COPY entrypoint.sh /opt/beaconhunt/entrypoint.sh
RUN chmod +x /opt/beaconhunt/entrypoint.sh

EXPOSE 53/tcp 53/udp
ENTRYPOINT ["/opt/beaconhunt/entrypoint.sh"]
