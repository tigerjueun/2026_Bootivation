#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/Bootivation/rpi_tray_single"
python3 single_slot_counter_zmq_audio.py --bind 'tcp://*:5562' --command-bind 'tcp://*:5563'
