FROM debian:12-slim

# Training SSH target for BeaconHunt. Ships HARDENED by default; the range only
# becomes vulnerable when BeaconHunt plants artifacts into it at deploy time.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        openssh-server curl cron ca-certificates procps iproute2 sudo \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /run/sshd /opt/beaconhunt/plant

# Legitimate defender/admin account (NOT a planted finding). This is your
# blue-team login: SSH in as 'defender' and use sudo to inspect and remediate,
# just like you'd have admin on your own CCDC box. Override at build time with
# --build-arg DEFENDER_PASSWORD=...
ARG DEFENDER_USER=defender
ARG DEFENDER_PASSWORD=defender
RUN useradd -m -s /bin/bash "$DEFENDER_USER" \
    && echo "$DEFENDER_USER:$DEFENDER_PASSWORD" | chpasswd \
    && usermod -aG sudo "$DEFENDER_USER"

# Hardened baseline. Planted drop-ins under sshd_config.d/ override this later.
RUN sed -ri 's/^#?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -ri 's/^#?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && echo "Include /etc/ssh/sshd_config.d/*.conf" >> /etc/ssh/sshd_config \
    && mkdir -p /etc/ssh/sshd_config.d

COPY plant/ /opt/beaconhunt/plant/
RUN chmod +x /opt/beaconhunt/plant/*.sh

COPY entrypoint.sh /opt/beaconhunt/entrypoint.sh
RUN chmod +x /opt/beaconhunt/entrypoint.sh

EXPOSE 22
ENTRYPOINT ["/opt/beaconhunt/entrypoint.sh"]
