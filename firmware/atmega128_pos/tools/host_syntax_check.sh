#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cc -std=c11 -Wall -Wextra -Werror -Iinclude -Itools/mock_avr -c src/*.c tools/mock_avr/mock_regs.c
rm -f ./*.o src/*.o tools/mock_avr/*.o
printf 'Host syntax check passed. This is not an AVR link/build.\n'
