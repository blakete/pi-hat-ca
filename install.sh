#!/usr/bin/env bash
# Install (or remove) the pi-hat-ca Game of Life as a systemd service
# so it starts automatically on boot.
#
# Usage:
#   ./install.sh            install + enable + start now
#   ./install.sh uninstall  stop + disable + remove service and config
#
# Runtime options (color, speed) live in /etc/default/pi-hat-ca.
# Edit that file, then: sudo systemctl restart pi-hat-ca
set -euo pipefail

SERVICE=pi-hat-ca
UNIT=/etc/systemd/system/${SERVICE}.service
ENV_FILE=/etc/default/${SERVICE}
REPO_DIR=$(cd "$(dirname "$0")" && pwd)

if [[ ${1:-install} == uninstall ]]; then
    sudo systemctl disable --now "$SERVICE" 2>/dev/null || true
    sudo rm -f "$UNIT" "$ENV_FILE"
    sudo systemctl daemon-reload
    echo "Removed $SERVICE service and $ENV_FILE."
    exit 0
fi

# Seed the config file with defaults, but never clobber existing settings.
if [[ ! -f $ENV_FILE ]]; then
    sudo tee "$ENV_FILE" > /dev/null <<'EOF'
# Options for the pi-hat-ca service (life.py). After editing, run:
#   sudo systemctl restart pi-hat-ca
LIFE_OPTS=--color 237,100,228 --speed 2
EOF
    echo "Created $ENV_FILE with default options."
fi

sudo tee "$UNIT" > /dev/null <<EOF
[Unit]
Description=Conway's Game of Life on the Sense HAT LED matrix
After=local-fs.target

[Service]
Type=simple
User=$(id -un)
EnvironmentFile=-${ENV_FILE}
ExecStart=/usr/bin/python3 ${REPO_DIR}/life.py \$LIFE_OPTS
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE"
sudo systemctl restart "$SERVICE"
echo "Installed and started. Options: $ENV_FILE | Status: systemctl status $SERVICE"
