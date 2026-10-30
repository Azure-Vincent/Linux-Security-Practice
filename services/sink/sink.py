#!/usr/bin/env python3
"""BeaconHunt local sink.

A tiny HTTP server that stands in for an attacker's C2. Planted "beacons" in the
range call back here instead of the internet, so the training is fully
contained. The sink only logs the hits (timestamp, source, query) to stdout and
to /var/log/beacons.log; it never issues commands or payloads back.
"""

from __future__ import annotations

import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOG_PATH = "/var/log/beacons.log"


class Handler(BaseHTTPRequestHandler):
    def _log_hit(self) -> None:
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        line = f"{ts} {self.client_address[0]} {self.command} {self.path}"
        print(line, flush=True)
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        self._log_hit()
        self.send_response(204)
        self.end_headers()

    do_POST = do_GET

    def log_message(self, *_args) -> None:
        # Silence the default stderr logging; we log our own line.
        return


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 9000), Handler)
    print("beaconhunt sink listening on :9000 (local range only)", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
