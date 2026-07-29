
# Protocol summary

| 구간 | 방식 | 포트/속도 | 핵심 데이터 |
|---|---|---|---|
| POS → Fusion | UART | COM5 / 57600 | `USER`, `PAY`, `COUNT`, `PAY_DONE` |
| Fusion → Rider | Bluetooth SPP serial | COM10 / 9600 | `SERVO:*`, `LED:*`, `RESET` |
| Vision → Fusion | ZMQ PUB/SUB | 5555 | `retail {JSON}` |
| RPi → Fusion | ZMQ PUB/SUB | 5562 | `TRAY_COUNT` JSON |
| Fusion → RPi | ZMQ PUSH/PULL | 5563 | audio/session JSON |
| Fusion → Vision | planned PUSH/PULL | 5557 | `CAPTURE_EVIDENCE` |

세부 문서는 각 모듈의 README와 `vision/contracts/`를 참고합니다.
