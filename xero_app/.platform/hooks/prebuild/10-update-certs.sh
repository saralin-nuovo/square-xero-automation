#!/usr/bin/env bash
set -euo pipefail

# Install/refresh CA certificates (dnf on AL2023, yum fallback)
if command -v dnf >/dev/null 2>&1; then
  dnf install -y ca-certificates || true
else
  yum install -y ca-certificates || true
fi

update-ca-trust force-enable || true
update-ca-trust extract || true

# Make sure Python/requests know where the system CA bundle is
export SSL_CERT_FILE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
