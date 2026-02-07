#!/bin/bash
#
# SSL Zertifikate für Development generieren
#

set -e

CERT_DIR="${1:-./certs}"
mkdir -p "$CERT_DIR"

echo "🔒 Generating SSL certificates for development..."

# Self-signed Zertifikat generieren
openssl req -x509 \
    -newkey rsa:4096 \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -days 365 \
    -nodes \
    -subj "/C=DE/ST=Berlin/L=Berlin/O=Zen-AI-Pentest/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1,IP:::1"

echo "✅ SSL certificates generated in $CERT_DIR:"
echo "  - cert.pem (Certificate)"
echo "  - key.pem (Private Key)"
echo ""
echo "📋 To start with HTTPS:"
echo "  docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d nginx"
echo ""
echo "🌐 Access: https://localhost"
