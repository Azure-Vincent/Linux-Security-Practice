FROM mariadb:11

# Training database target for BeaconHunt (MariaDB). The baseline schema is
# created hardened; BeaconHunt plants the rogue users / grants / triggers at
# deploy time via the plant dispatcher.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        sudo procps iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/beaconhunt/plant

# Legitimate defender/admin OS account (NOT a planted finding). SSH is not
# exposed here; use `docker compose exec db bash` (root) or sudo. The DATABASE
# admin is the MariaDB root user (password from MARIADB_ROOT_PASSWORD).
ARG DEFENDER_USER=defender
ARG DEFENDER_PASSWORD=defender
RUN useradd -m -s /bin/bash "$DEFENDER_USER" \
    && echo "$DEFENDER_USER:$DEFENDER_PASSWORD" | chpasswd \
    && usermod -aG sudo "$DEFENDER_USER"

# Baseline schema + least-privilege app user, loaded on first init.
COPY initdb/ /docker-entrypoint-initdb.d/
COPY plant/ /opt/beaconhunt/plant/
RUN chmod +x /opt/beaconhunt/plant/*.sh

EXPOSE 3306
