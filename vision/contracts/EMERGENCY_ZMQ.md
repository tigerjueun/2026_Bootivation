# Fusion → Vision WebUI Emergency Contract (`5556`)

도율님 Vision WebUI 최종 구현은 외부 시스템이 절도·미결제 의심 고객의 ID를 보내면, 해당 고객의 Camera 1 입장 스냅샷을 찾아 WebUI에 경보와 함께 표시합니다.

- Vision WebUI: ZMQ `REP`, `tcp://*:5556`
- Fusion: ZMQ `REQ`, `tcp://<VISION_PC_IP>:5556`
- Format: JSON
- ROS dependency: Emergency 요청/응답 자체에는 불필요
- Requirement: Vision `webUI/server.py`가 실행 중이어야 함

## 1. Request

```json
{
  "Emergency": true,
  "customer_id": 100,
  "timestamp": 1784902700.2
}
```

| Field | Type | Required | Description |
|---|---:|---:|---|
| `Emergency` | bool | yes | 반드시 JSON boolean `true` |
| `customer_id` | int | yes | 절도·미결제 의심 고객의 전역 ID |
| `timestamp` | float | no | Fusion 경보 시각, 없으면 Vision 수신 시각 사용 |

Vision은 `customer_id`, `customerID`, `CustomerID`를 호환하지만 Fusion은 `customer_id`로 통일합니다.

Request schema: [`shared/schemas/emergency_request.schema.json`](../../shared/schemas/emergency_request.schema.json)

## 2. Success response

Entry snapshot available:

```json
{
  "ok": true,
  "customer_id": 100,
  "snapshot_available": true
}
```

No matching JPEG:

```json
{
  "ok": true,
  "customer_id": 100,
  "snapshot_available": false
}
```

`snapshot_available=false`여도 WebUI에는 절도 경보와 고객 ID가 표시되며, 사진 영역에는 스냅샷 부재 안내가 나타납니다.

Response schema: [`shared/schemas/emergency_response.schema.json`](../../shared/schemas/emergency_response.schema.json)

## 3. Error response

```json
{
  "ok": false,
  "error": "Emergency must be true"
}
```

## 4. Vision-side behavior

```text
1. JSON 객체인지 검증
2. Emergency == true 확인
3. customer_id 정수 변환
4. Camera 1 entry JPEG 검색
5. REP response 송신
6. WebSocket emergency event 송신
7. WebUI에 큰 빨간 절도 경보 표시
8. customer_id와 입장 이미지 표시
```

Default snapshot directory:

```text
/tmp/bootivation_customer_captures
```

Filename example:

```text
customer_100_entry_1784902629000.jpg
```

## 5. Fusion client example

```python
from __future__ import annotations

import time
import zmq


def send_emergency(
    endpoint: str,
    customer_id: int,
    *,
    timeout_ms: int = 3000,
) -> dict:
    context = zmq.Context.instance()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.LINGER, 0)
    socket.setsockopt(zmq.SNDTIMEO, timeout_ms)
    socket.setsockopt(zmq.RCVTIMEO, timeout_ms)
    socket.connect(endpoint)

    try:
        socket.send_json({
            "Emergency": True,
            "customer_id": int(customer_id),
            "timestamp": time.time(),
        })
        response = socket.recv_json()
        if not isinstance(response, dict):
            raise RuntimeError("Vision returned a non-object response")
        return response
    finally:
        socket.close(0)
```

Usage:

```python
response = send_emergency(
    "tcp://192.168.0.20:5556",
    100,
)
print(response)
```

A ready-to-run CLI is provided at [`fusion_pc/tools/send_vision_emergency.py`](../../fusion_pc/tools/send_vision_emergency.py).

## 6. REQ/REP rules

- REQ는 요청 후 반드시 REP 응답을 받아야 다음 요청을 보낼 수 있습니다.
- timeout 후 같은 REQ 소켓에서 재전송하지 말고 소켓을 닫아 새로 생성합니다.
- `LINGER=0`, send/receive timeout을 설정해 종료 시 멈춤을 방지합니다.
- 같은 고객에 대한 경보는 Fusion에서 latch/debounce해 반복 팝업을 막습니다.
- 현재 프로토콜은 인증과 암호화를 제공하지 않습니다.
- 5556은 신뢰 가능한 내부망에만 열고 Fusion PC IP만 firewall allow하는 것을 권장합니다.

## 7. Local Vision test

Vision WebUI가 실행 중일 때 Vision PC에서:

```bash
python3 - <<'PY'
import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.setsockopt(zmq.RCVTIMEO, 3000)
socket.connect("tcp://127.0.0.1:5556")
socket.send_json({"Emergency": True, "customer_id": 100})
print(socket.recv_json())
socket.close()
context.term()
PY
```

Check listener:

```bash
ss -ltnp | grep ':5556'
```
