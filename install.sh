#!/usr/bin/env bash
# Install (or remove) the pi-hat-ca Game of Life as a systemd service
# so it starts automatically on boot.
#
# Usage:
#   ./install.sh            install + enable + start now
#   ./install.sh uninstall  stop + disable + remove the service
set -euo pipefail

SERVICE=pi-hat-ca
UNIT=/etc/systemd/system/${SERVICE}.service
REPO_DIR=$(cd "$(dirname "$0")" && pwd)

if [[ ${1:-install} == uninstall ]]; then
    sudo systemctl disable --now "$SERVICE" 2>/dev/null || true
    sudo rm -f "$UNIT"
    sudo systemctl daemon-reload
    echo "Removed $SERVICE service."
    exit 0
fi

sudo tee "$UNIT" > /dev/null <<EOF
[Unit]
Description=Conway's Game of Life on the Sense HAT LED matrix
After=local-fs.target

[Service]
Type=simple
User=$(id -un)
ExecStart=/usr/bin/python3 ${REPO_DIR}/life.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE"
echo "Installed and started. Check with: systemctl status $SERVICE"
