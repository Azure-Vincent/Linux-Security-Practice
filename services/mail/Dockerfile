FROM debian:12-slim

# Training mail target for BeaconHunt (Postfix SMTP + Dovecot IMAP/POP3).
# Ships HARDENED; BeaconHunt plants the open relay / weak creds / alias &
# forward backdoors at deploy time. Detection is file-based, so the range works
# even if a mail daemon is slow to start.
RUN echo "postfix postfix/main_mailer_type select Internet Site" | debconf-set-selections \
    && echo "postfix postfix/mailname string mail.acme.local" | debconf-set-selections \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        postfix dovecot-imapd dovecot-pop3d dovecot-core rsyslog \
        cron curl sudo procps iproute2 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/beaconhunt/plant

# Legitimate defender/admin account (NOT a planted finding). No SSH here; use
# `docker compose exec mail bash` (root) or sudo.
ARG DEFENDER_USER=defender
ARG DEFENDER_PASSWORD=defender
RUN useradd -m -s /bin/bash "$DEFENDER_USER" \
    && echo "$DEFENDER_USER:$DEFENDER_PASSWORD" | chpasswd \
    && usermod -aG sudo "$DEFENDER_USER"

# Baseline mailbox users with strong passwords (not findings).
RUN for u in alice bob; do \
        useradd -m -s /usr/sbin/nologin "$u" \
        && echo "$u:Str0ng-$u-Pw9x" | chpasswd ; \
    done

COPY plant/ /opt/beaconhunt/plant/
RUN chmod +x /opt/beaconhunt/plant/*.sh
COPY entrypoint.sh /opt/beaconhunt/entrypoint.sh
RUN chmod +x /opt/beaconhunt/entrypoint.sh

EXPOSE 25 143
ENTRYPOINT ["/opt/beaconhunt/entrypoint.sh"]
