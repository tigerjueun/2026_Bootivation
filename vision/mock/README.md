# Vision ZMQ Mocks

ROS 2와 실제 카메라 없이 Fusion의 최종 Vision 계약을 시험하기 위한 도구입니다.

## 1. Customer POS/EXIT publisher

Ubuntu/Linux/Windows:

```bash
python3 -m pip install pyzmq
python3 retail_transition_pub.py --bind 'tcp://*:5555'
```

Fusion을 먼저 실행하고 약 1초 뒤 입력합니다.

```text
pos 100 A=2,B=1,C=1
exit 100 A=2,B=1,C=1
```

실제 wire message:

```text
retail {"timestamp":...,"customer_id":100,"state":"POS",...}
```

## 2. Emergency responder

```bash
python3 emergency_rep.py --bind 'tcp://*:5556' --snapshot-available
```

Fusion PC에서:

```powershell
py .\fusion_pc\tools\send_vision_emergency.py 100 `
  --endpoint tcp://VISION_MOCK_IP:5556
```

Expected:

```json
{
  "ok": true,
  "customer_id": 100,
  "snapshot_available": true
}
```

## 3. Legacy manual removal publisher

`vision_zmq_manual_pub.py`는 개발 중 사용한 `REMOVE_CANDIDATE:A/B/C` 직접 송신 도구입니다. 최종 ROS upstream wire protocol은 이 형식이 아니라 `retail {JSON}` POS/EXIT transition입니다.
