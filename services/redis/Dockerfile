FROM redis:7

# Training Redis target for BeaconHunt. Ships HARDENED (loopback bind,
# protected-mode on, password set); BeaconHunt plants the no-auth / weak-pass /
# rogue-key / persistence findings at deploy time. Detection is file/command
# based, so the range works even if redis-server is slow to start.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        cron curl sudo procps iproute2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/beaconhunt/plant /data /etc/redis

# Legitimate defender/admin account (NOT a planted finding). No SSH here; use
# `docker compose exec redis bash` (root) or sudo. The Redis admin password is
# in REDIS_PASSWORD (see compose).
ARG DEFENDER_USER=defender
ARG DEFENDER_PASSWORD=defender
RUN useradd -m -s /bin/bash "$DEFENDER_USER" \
    && echo "$DEFENDER_USER:$DEFENDER_PASSWORD" | chpasswd \
    && usermod -aG sudo "$DEFENDER_USER"

COPY redis.conf /etc/redis/redis.conf
COPY plant/ /opt/beaconhunt/plant/
RUN chmod +x /opt/beaconhunt/plant/*.sh
COPY entrypoint.sh /opt/beaconhunt/entrypoint.sh
RUN chmod +x /opt/beaconhunt/entrypoint.sh

EXPOSE 6379
ENTRYPOINT ["/opt/beaconhunt/entrypoint.sh"]
