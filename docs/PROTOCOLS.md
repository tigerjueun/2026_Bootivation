# Communication Protocols

## 1. Channel summary

| Direction | Pattern | Port / speed | Payload |
|---|---|---:|---|
| Vision → Fusion | ZMQ PUB/SUB | `5555` | `retail {JSON}` customer POS/EXIT transition |
| Fusion → Vision WebUI | ZMQ REQ/REP | `5556` | Emergency request and snapshot availability response |
| RPi → Fusion | ZMQ PUB/SUB | `5562` | `TRAY_COUNT` JSON |
| Fusion → RPi | ZMQ PUSH/PULL | `5563` | session and audio command JSON |
| POS → Fusion | UART | `COM5 / 57600 8N1` | CSV-like line protocol |
| Fusion → Rider | Bluetooth SPP serial | `COM10 / 9600` | one command per line |
| Fusion → Browser | HTTP | `8088` | operations dashboard |
| Vision WebUI → Browser | HTTP/WebSocket | `8080` | CCTV, tracking, ROI, Emergency |

---

## 2. Vision customer state — 5555

### Transport

```text
Vision: ZMQ PUB tcp://*:5555
Fusion: ZMQ SUB tcp://VISION_PC_IP:5555
Subscription prefix: "retail "
Encoding: UTF-8
Frame: one string frame
```

Message format:

```text
retail {"timestamp":1784902657.924002,"customer_id":100,"state":"POS",...}
```

### Required fields

| Field | Type | Description |
|---|---:|---|
| `timestamp` | float | event timestamp |
| `customer_id` | int | global customer ID |
| `state` | string | `POS` or `EXIT` |
| `active` | bool | active visit flag |
| `visit_state` | string | `entering`, `inside`, `exiting`, `released`, ... |
| `zone_A_picks` | int | cumulative A picks |
| `zone_B_picks` | int | cumulative B picks |
| `zone_C_picks` | int | cumulative C picks |
| `at_kiosk` | bool | kiosk confirmation |
| `event` | string/null | exit reason such as `exit` |

POS example:

```json
{
  "timestamp": 1784902657.924002,
  "customer_id": 100,
  "state": "POS",
  "active": true,
  "visit_state": "inside",
  "zone_A_picks": 2,
  "zone_B_picks": 1,
  "zone_C_picks": 1,
  "at_kiosk": true,
  "event": null
}
```

EXIT example:

```json
{
  "timestamp": 1784902700.1,
  "customer_id": 100,
  "state": "EXIT",
  "active": false,
  "visit_state": "released",
  "zone_A_picks": 2,
  "zone_B_picks": 1,
  "zone_C_picks": 1,
  "at_kiosk": true,
  "event": "exit"
}
```

### Final upstream semantics

- `state=POS`: 키오스크 최초 확정 시 한 번
- `state=EXIT`: 퇴장 확정 시 한 번
- 최종 upstream은 입장·매장 이동·매 프레임 상태를 5555로 주기 송신하지 않습니다.
- POS 이후 PICK 수량이 변해도 POS 패킷을 다시 보내지 않으며 EXIT 패킷이 최종 수량입니다.
- Fusion은 `customer_id`를 키로 POS 상태와 결제 장부를 보관한 뒤 EXIT에서 최종 비교해야 합니다.
- PUB/SUB에는 ACK·재전송·과거 패킷 복구가 없으므로 **Fusion SUB를 먼저 실행**해야 합니다.

Schema: [`shared/schemas/retail_customer_state.schema.json`](../shared/schemas/retail_customer_state.schema.json)

---

## 3. Vision Emergency — 5556

### Transport

```text
Fusion: ZMQ REQ tcp://VISION_PC_IP:5556
Vision WebUI: ZMQ REP tcp://*:5556
```

Request:

```json
{
  "Emergency": true,
  "customer_id": 100,
  "timestamp": 1784902700.2
}
```

`customer_id`, `customerID`, `CustomerID`를 수신 측에서 호환하지만, 송신은 `customer_id`를 사용합니다.

Response when an entry snapshot exists:

```json
{
  "ok": true,
  "customer_id": 100,
  "snapshot_available": true
}
```

Response when the customer ID is valid but no JPEG exists:

```json
{
  "ok": true,
  "customer_id": 100,
  "snapshot_available": false
}
```

Invalid request:

```json
{
  "ok": false,
  "error": "Emergency must be true"
}
```

Vision WebUI processing:

```text
REQ received
→ validate JSON and customer_id
→ search /tmp/bootivation_customer_captures
→ return REP
→ WebSocket alert
→ show large red theft warning + customer entry image
```

Schema: [`shared/schemas/emergency_request.schema.json`](../shared/schemas/emergency_request.schema.json)

REQ/REP requires strict send→receive order. On timeout, close the old REQ socket and create a new one before retrying.

---

## 4. POS UART — COM5 57600

### Startup and session

```text
BOOT,ATMEGA128_POS_C
SESSION,START,ID=1
EVT,WAIT_PERSON
HELLO
EVT,PERSON_DETECTED
EVT,SELECT_USER
USER,CUSTOMER
```

### Product and payment

```text
EVT,PRODUCT_DETECTED
EVT,TOUCH_A
PAY:A
COUNT,A=1,B=0,C=0,TOTAL=1
```

Completion sends two lines:

```text
PAY_DONE
PAY_DONE,USER=CUSTOMER,A=1,B=2,C=1,TOTAL=4,SESSION=2
```

Fusion must count this as **one payment batch**. The detailed line reconciles quantities and session ID; it must not add a second payment.

Manual POS reset:

```text
SESSION_RESET
```

Uncommitted session quantities are rolled back, while confirmed physical Vision removals remain unchanged.

---

## 5. Rider Arduino — COM10 9600

One ASCII command plus LF per message:

```text
PING
GET_STATUS
SERVO:A
SERVO:B
SERVO:C
SERVO:HOME
LED:BLUE
LED:RED
LED:GREEN
LED:OFF
RESET
```

Final calibrated angles:

```text
A=85, B=45, C=0, HOME=150
```

Fusion inserts a short gap between consecutive LED and servo commands because HC-06/SoftwareSerial may miss tightly packed messages.

---

## 6. Raspberry Pi tray state — 5562

```json
{
  "version": "1.1",
  "source": "rpi_tray",
  "event": "TRAY_COUNT",
  "timestamp_ms": 1784862000123,
  "sequence": 42,
  "layout": "2x2",
  "before": {"A": 1, "B": 1, "C": 0, "EMPTY": 2},
  "after": {"A": 0, "B": 1, "C": 0, "EMPTY": 3},
  "before_slots": ["A", "B", "EMPTY", "EMPTY"],
  "after_slots": ["EMPTY", "B", "EMPTY", "EMPTY"],
  "audio_state": {
    "last_audio": "SCAN_PRODUCT",
    "result": "SCANNING",
    "expected": null
  }
}
```

Fusion uses the latest stable state; logs should not assume every frame is stored.

---

## 7. Fusion commands to Raspberry Pi — 5563

Payment confirmed:

```json
{
  "command": "PAYMENT_CONFIRMED",
  "expected": {"A": 1, "B": 1, "C": 1}
}
```

Reset:

```json
{"command": "SYSTEM_RESET"}
```

Manual audio:

```json
{
  "command": "PLAY_AUDIO",
  "event": "TRAY_MISMATCH"
}
```

Supported audio events:

```text
SYSTEM_READY
PLACE_BEFORE
SCAN_PRODUCT
SCAN_COMPLETED
TRAY_MISMATCH
SYSTEM_RESET
```

---

## 8. Security and reliability notes

- ZMQ channels currently have no authentication or encryption.
- Use a trusted private network and restrict 5555/5556/5562/5563 with a firewall.
- 5555 PUB/SUB is lossy by design; one-shot POS/EXIT packets are especially sensitive to startup order.
- 5556 REQ/REP must use timeouts and socket recreation after failure.
- Do not store school credentials, passwords, tokens, or personal IP addresses in committed config files.
