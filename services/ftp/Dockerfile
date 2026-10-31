FROM debian:12-slim

# Training FTP target for BeaconHunt (vsftpd). Ships HARDENED (no anonymous,
# chroot on, writes off); BeaconHunt plants the loose config / backdoors at
# deploy time. Detection is file-based, so the range works even if the daemon
# is finicky.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        vsftpd cron curl sudo procps iproute2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/beaconhunt/plant /srv/ftp /var/run/vsftpd/empty

# Legitimate defender/admin account (NOT a planted finding). No SSH here; use
# `docker compose exec ftp bash` (root) or sudo.
ARG DEFENDER_USER=defender
ARG DEFENDER_PASSWORD=defender
RUN useradd -m -s /bin/bash "$DEFENDER_USER" \
    && echo "$DEFENDER_USER:$DEFENDER_PASSWORD" | chpasswd \
    && usermod -aG sudo "$DEFENDER_USER"

# Baseline FTP account with a strong password (not a finding).
RUN useradd -m -d /srv/ftp/acme -s /usr/sbin/nologin acme-ftp \
    && echo "acme-ftp:Str0ng-Ftp-Pw9x" | chpasswd

COPY vsftpd.conf /etc/vsftpd.conf
COPY plant/ /opt/beaconhunt/plant/
RUN chmod +x /opt/beaconhunt/plant/*.sh
COPY entrypoint.sh /opt/beaconhunt/entrypoint.sh
RUN chmod +x /opt/beaconhunt/entrypoint.sh

EXPOSE 21
ENTRYPOINT ["/opt/beaconhunt/entrypoint.sh"]
