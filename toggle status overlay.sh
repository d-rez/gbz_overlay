#!/bin/bash

if systemctl is-active --quiet retropie-status-overlay; then
  sudo service retropie-status-overlay stop
else
  sudo service retropie-status-overlay start
fi
