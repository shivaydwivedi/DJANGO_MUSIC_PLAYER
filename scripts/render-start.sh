#!/usr/bin/env bash
set -o errexit

exec waitress-serve \
  --listen="0.0.0.0:${PORT:-10000}" \
  --trusted-proxy="*" \
  --trusted-proxy-headers="x-forwarded-proto" \
  musicplayer.wsgi:application
