FROM debian:12-slim

# Training SMB target for BeaconHunt (Samba). Ships HARDENED (no guest access,
# no loose shares); BeaconHunt plants the bad shares / scripts / users at deploy.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        samba samba-common-bin cron curl sudo procps iproute2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/beaconhunt/plant /var/log/samba /etc/samba/scripts

# Legitimate defender/admin OS account (NOT a planted finding). SSH is not
# exposed here; use `docker compose exec smb bash` (root) or sudo.
ARG DEFENDER_USER=defender
ARG DEFENDER_PASSWORD=defender
RUN useradd -m -s /bin/bash "$DEFENDER_USER" \
    && echo "$DEFENDER_USER:$DEFENDER_PASSWORD" | chpasswd \
    && usermod -aG sudo "$DEFENDER_USER"

COPY smb.conf /etc/samba/smb.conf
COPY plant/ /opt/beaconhunt/plant/
RUN chmod +x /opt/beaconhunt/plant/*.sh
COPY entrypoint.sh /opt/beaconhunt/entrypoint.sh
RUN chmod +x /opt/beaconhunt/entrypoint.sh

EXPOSE 445
ENTRYPOINT ["/opt/beaconhunt/entrypoint.sh"]
