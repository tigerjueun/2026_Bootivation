# Vision → Fusion Customer State Contract (`5555`)

본 문서는 [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv)의 최종 ZMQ 고객 상태 송신 규격을 Bootivation Fusion 관점에서 정리합니다.

- Upstream archive commit: [`3d9225e`](https://github.com/Kuz-DX/ssg-ssac-cctv/commit/3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef)
- Vision socket: ZMQ `PUB`, `tcp://*:5555`
- Fusion socket: ZMQ `SUB`, `tcp://<VISION_PC_IP>:5555`
- Topic prefix: `retail`
- Subscription string: `retail ` — 뒤의 공백 포함
- Frame: UTF-8 단일 문자열

## 1. Wire format

```text
retail {"timestamp":1784902657.924002,"customer_id":100,"state":"POS",...}
```

수신 측은 첫 번째 공백만 기준으로 분리합니다.

```python
topic, json_text = raw_message.split(" ", 1)
assert topic == "retail"
payload = json.loads(json_text)
```

## 2. Required payload

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

| Field | Type | Meaning |
|---|---:|---|
| `timestamp` | float | ROS 또는 카메라 기준 상태 시각 |
| `customer_id` | int | 카메라 간 공유되는 전역 고객 ID |
| `state` | string | 외부 전환 상태, `POS` 또는 `EXIT` |
| `active` | bool | 현재 방문이 활성 상태인지 여부 |
| `visit_state` | string | `entering`, `inside`, `exiting`, `released` 등 내부 lifecycle |
| `zone_A_picks` | int | 상품 A 누적 PICK 수량 |
| `zone_B_picks` | int | 상품 B 누적 PICK 수량 |
| `zone_C_picks` | int | 상품 C 누적 PICK 수량 |
| `at_kiosk` | bool | 키오스크 접근 확정 여부 |
| `event` | string/null | 종료 원인, 정상 퇴장은 `exit` |

JSON Schema: [`shared/schemas/retail_customer_state.schema.json`](../../shared/schemas/retail_customer_state.schema.json)

## 3. State semantics

최종 upstream의 `customer_state_filter`는 모든 프레임을 보내지 않고, 고객별로 아래 전환만 각각 한 번 송신합니다.

### POS transition

```json
{
  "state": "POS",
  "active": true,
  "at_kiosk": true
}
```

고객이 키오스크에 처음 확정된 순간 발행됩니다. Fusion은 이 패킷을 `customer_id` 기준으로 보관하고 이후 POS 결제 세션과 연결합니다.

### EXIT transition

```json
{
  "state": "EXIT",
  "active": false,
  "event": "exit"
}
```

고객 퇴장이 확정된 순간 발행됩니다. 이 패킷의 `zone_*_picks`가 해당 방문의 최종 PICK 수량입니다.

## 4. Important integration rule

최종 규격은 과거 개발 중 사용했던 주기 상태 스트림과 다릅니다.

```text
과거 가정
A picks: 0 → 1 → 2를 여러 패킷으로 받아 증가분 계산

최종 upstream
POS 전환 한 번 + EXIT 전환 한 번
EXIT 패킷의 최종 A/B/C 수량을 고객 결제 장부와 비교
```

따라서 Fusion은 다음과 같이 처리해야 합니다.

```text
state=POS
→ active_customer[customer_id] 저장
→ 이후 ATmega128 CUSTOMER 결제 수량을 같은 customer_id에 귀속

state=EXIT
→ picked = EXIT의 zone_A/B/C_picks
→ paid = 해당 customer_id에 캐시한 POS 결제 수량
→ unpaid = max(picked - paid, 0)
→ 정상 / 부분 결제 / 완전 미결제 판정
→ 세션 정리
```

POS 패킷 이후 PICK 수량이 바뀌더라도 POS 패킷은 다시 발행되지 않습니다. EXIT 패킷을 최종 수량으로 신뢰해야 합니다.

## 5. Subscriber example

```python
#!/usr/bin/env python3

import json
import zmq

VISION_PC_IP = "192.168.0.20"
TOPIC = "retail"

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.LINGER, 0)
socket.setsockopt_string(zmq.SUBSCRIBE, TOPIC + " ")
socket.connect(f"tcp://{VISION_PC_IP}:5555")

customers = {}

try:
    while True:
        raw = socket.recv_string()
        topic, body = raw.split(" ", 1)
        if topic != TOPIC:
            continue

        customer = json.loads(body)
        customer_id = int(customer["customer_id"])

        if customer["state"] == "POS":
            customers[customer_id] = customer
            print("[POS]", customer)
        elif customer["state"] == "EXIT":
            final_customer = customer
            customers.pop(customer_id, None)
            print("[EXIT]", final_customer)
finally:
    socket.close()
    context.term()
```

## 6. Publisher startup

`run_model_test.sh`는 최종 ZMQ transmitter를 자동으로 시작하지 않습니다. Vision PC에서 별도 터미널로 실행합니다.

```bash
cd /home/kuzdx/bootivation
source /opt/ros/humble/setup.bash

PYTHONPATH="$PWD/perception/src/retail_perception${PYTHONPATH:+:$PYTHONPATH}" \
python3 -c 'from retail_perception.zmq_transmitter_node import main; main()' \
  --ros-args \
  --params-file "$PWD/perception/src/retail_perception/config/pipeline.yaml"
```

Expected:

```text
Publishing customer states on tcp://*:5555
```

## 7. Delivery limitations

- ZMQ PUB/SUB에는 ACK와 재전송이 없습니다.
- Fusion SUB 연결 전에 발행된 POS/EXIT 패킷은 복구되지 않습니다.
- 네트워크 단절 중 발생한 패킷도 재전송되지 않습니다.
- POS와 EXIT가 각각 한 번만 발행되므로 **Fusion을 먼저 실행**해야 합니다.
- 전달 보장이 필요하면 향후 sequence/ACK 또는 durable message broker를 추가해야 합니다.
- 현재 프로토콜에는 인증·암호화가 없으므로 신뢰 가능한 내부망과 방화벽을 사용합니다.
