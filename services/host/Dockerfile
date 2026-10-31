FROM debian:12-slim

# Generic Linux "host" target for BeaconHunt — the box that carries host-level
# compromises (rogue accounts, sudoers, systemd timers, anti-forensics,
# unexpected listeners). Ships HARDENED; findings are planted at deploy time.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        openssh-server curl cron sudo procps iproute2 ca-certificates socat \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /run/sshd /opt/beaconhunt/plant /etc/systemd/system

RUN sed -ri 's/^#?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# Legitimate defender/admin account (NOT a planted finding).
ARG DEFENDER_USER=defender
ARG DEFENDER_PASSWORD=defender
RUN useradd -m -s /bin/bash "$DEFENDER_USER" \
    && echo "$DEFENDER_USER:$DEFENDER_PASSWORD" | chpasswd \
    && usermod -aG sudo "$DEFENDER_USER"

COPY plant/ /opt/beaconhunt/plant/
RUN chmod +x /opt/beaconhunt/plant/*.sh
COPY entrypoint.sh /opt/beaconhunt/entrypoint.sh
RUN chmod +x /opt/beaconhunt/entrypoint.sh

EXPOSE 22
ENTRYPOINT ["/opt/beaconhunt/entrypoint.sh"]
