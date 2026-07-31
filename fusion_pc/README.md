# Fusion PC

Windows에서 POS, Rider, Raspberry Pi, ROS 2 Vision을 하나의 상태머신으로 결합하는 중앙 모듈입니다.

## Connected systems

```text
ATmega128 POS        COM5 / 57600
Arduino Rider        COM10 / 9600
RPi tray             SUB 5562 / PUSH 5563
Vision customer      SUB 5555 / topic "retail "
Vision Emergency     REQ 5556
Operations dashboard HTTP 8088
```

## Install

```powershell
cd fusion_pc
py -m pip install -r .\requirements.txt
Copy-Item .\config\system.example.json .\config\system.json
notepad .\config\system.json
```

Configure the Vision PC address in both fields:

```json
"vision": {
  "enabled": true,
  "subscriber_endpoint": "tcp://VISION_PC_IP:5555",
  "emergency_endpoint": "tcp://VISION_PC_IP:5556",
  "topic": "retail"
}
```

## Run

```powershell
py .\main.py `
  --config .\config\system.json `
  --rpi-endpoint tcp://10.77.0.2:5562 `
  --rpi-command-endpoint tcp://10.77.0.2:5563
```

The Emergency endpoint is normally read from the config. It can be overridden:

```powershell
py .\main.py `
  --config .\config\system.json `
  --vision-emergency-endpoint tcp://VISION_PC_IP:5556
```

Dashboard:

```text
http://127.0.0.1:8088
```

## Final customer correlation

The final Vision upstream publishes one `state=POS` transition and one `state=EXIT` transition per customer.

```text
POS packet
→ cache customer_id and prepare payment association

ATmega CUSTOMER PAY_DONE
→ store payment for that customer
→ send expected quantity to RPi tray

EXIT packet
→ use final A/B/C PICK counts
→ compare with cached payment
→ clear / partial payment / no payment
```

A short association window handles cases where the POS serial summary and Vision POS transition arrive in the opposite order.

## Critical unpaid action

```text
customer EXIT with unpaid items
→ operations dashboard CRITICAL alert
→ Rider LED RED
→ RPi TRAY_MISMATCH WAV
→ Vision Emergency REQ 5556
→ WebUI theft alert + entry snapshot
```

The 5556 client runs in a background dispatcher, so a Vision timeout does not block the central event loop.

## Console commands

```text
status
rpi
vision
order A=1,B=1,C=1
event REMOVE_CANDIDATE:A
audio TRAY_MISMATCH
rpi-reset
emergency 100
reset
quit
```

Manual `event` commands are for integration testing. Production Vision data arrives through `retail {JSON}` on port 5555.

## Tests

```powershell
py -m unittest discover -s .\tests -p "test_*.py" -v
```

Important references:

- [`../docs/PROTOCOLS.md`](../docs/PROTOCOLS.md)
- [`../vision/contracts/RETAIL_ZMQ.md`](../vision/contracts/RETAIL_ZMQ.md)
- [`../vision/contracts/EMERGENCY_ZMQ.md`](../vision/contracts/EMERGENCY_ZMQ.md)
