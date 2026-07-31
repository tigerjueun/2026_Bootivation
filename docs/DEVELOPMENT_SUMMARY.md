# Development Summary

Bootivation은 하나의 프레임워크 안에서 시작한 프로젝트가 아니라, 서로 다른 개발 환경과 하드웨어를 짧은 시간 안에 연결한 해커톤 프로젝트였습니다.

```text
Ubuntu ROS 2 Vision
Windows Python Fusion
ATmega128 AVR C
Arduino UNO / HC-06
Raspberry Pi / Picamera2 / OpenCV
App Inventor
```

이 문서는 최종 결과물뿐 아니라, 실제 통합 과정에서 발견한 문제와 해결 방향을 기록합니다.

---

## 1. Initial decomposition

팀은 시스템을 다음 책임으로 나누었습니다.

```text
Vision
고객·손·상품 인식, 추적, PICK, 키오스크/퇴장

POS
CUSTOMER/RIDER 상품 확인과 결제 장부

Rider device
상품 위치 화살표와 상태 LED

RPi tray
계산 전·후 상품 종류·수량 및 음성 안내

Fusion
모든 장부·상태·경보의 중앙 결합
```

이 분리는 병렬 개발을 가능하게 했지만, 각 파트가 같은 단어를 다르게 해석하는 문제가 생겼습니다. 특히 `Rider PAY`, `상품 제거`, `POS 확인`이 같은 사건인지 다른 사건인지 명확히 구분하는 작업이 중요했습니다.

---

## 2. POS protocol migration

### Problem

초기 POS는 ASM 기반이었고, 이후 C로 모듈화한 최종 펌웨어는 새 CSV 형태의 UART 메시지를 사용했습니다.

```text
USER,CUSTOMER
PAY:A
COUNT,A=1,B=0,C=0,TOTAL=1
PAY_DONE
PAY_DONE,USER=CUSTOMER,A=1,B=0,C=0,TOTAL=1,SESSION=1
```

Fusion의 기존 parser는 `MODE:CUSTOMER`, `PAY:A`, `PAY_DONE` 중심이어서 새 프로토콜을 바로 이해하지 못했습니다.

### Resolution

- 구형·신형 protocol parser를 동시에 지원
- session ID, phase, reported count를 Fusion state에 추가
- 일반 `PAY_DONE`과 상세 `PAY_DONE,...`를 하나의 완료로 처리
- 상세 요약은 이미 입력된 PAY를 다시 더하지 않고 reconciliation에 사용
- `SESSION_RESET` 시 완료되지 않은 POS 세션만 rollback

### Lesson

이벤트와 최종 snapshot을 동시에 보내는 프로토콜에서는 **increment event와 authoritative summary를 구분**해야 합니다.

---

## 3. Rider three-way verification

### Misinterpretation found during integration

초기 Fusion에서는 Rider POS의 `PAY:A/B/C`를 실제 선반 제거량으로 기록했습니다. 그러나 실제 서비스 흐름은 다음과 같았습니다.

```text
Vision shelf removal
→ 실제 수집량

Rider POS scan
→ 출점 전 최종 확인량
```

두 값은 같은 장부가 아니었습니다.

### Final ledgers

```text
order_items          주문량
rider_removed        Vision 실제 선반 제거량
rider_checked_items  Rider POS 최종 확인량
inventory_removed    실제 재고 감소량
```

Final condition:

```text
order_items == rider_removed == rider_checked_items
```

### Result

- Vision 수집 완료만으로 최종 PICKUP_COMPLETE를 내지 않음
- POS 확인 전에는 HOME/대기 상태
- 주문 외 상품 또는 초과 수량은 RED
- POS 확인이 부족하거나 초과하면 RED
- 세 장부가 일치할 때만 GREEN

### Lesson

장치가 같은 상품을 관찰하더라도 **관찰 목적이 다르면 별도 ledger가 필요**합니다.

---

## 4. HC-06 sequential command loss

### Symptom

Fusion log에는 다음이 모두 출력되었지만:

```text
[rider] TX LED:BLUE
[rider] TX SERVO:A
```

LED만 켜지고 서보가 움직이지 않는 경우가 있었습니다. COM10 direct test에서는 두 기능 모두 정상이었습니다.

### Root cause and mitigation

HC-06 + Arduino SoftwareSerial 환경에서 연속 명령과 ACK 송신이 너무 촘촘하면 다음 명령을 놓칠 수 있었습니다.

적용한 완화:

- Fusion Rider 명령 사이 약 0.30초 gap
- HC-06 수신 경로에서 불필요한 Bluetooth ACK 송신 최소화
- 명령 종료 LF 보장
- 서보 외부전원 및 공통 GND 사용

### Final calibration

```text
A=85°
B=45°
C=0°
HOME=150°
```

### Lesson

`serial.write()` 성공은 actuator 실행 성공과 동일하지 않습니다. 실제 장치에서는 command pacing과 reply direction까지 검증해야 합니다.

---

## 5. Raspberry Pi dual-camera fallback

### Initial plan

- IMX219 camera 0: 계산 전
- IMX219 camera 1: 계산 후

두 카메라가 처음에는 인식되었지만, 이후 한 CSI camera가 부팅 단계에서 등록되지 않는 문제가 재발했습니다.

### Investigation

- config overlay 확인
- 케이블·카메라 swap
- camera list 및 dmesg 확인
- buffer/RAW stream 부담 확인
- 단독 포트 시험

### Final fallback

대회 시간 안에 안정적인 결과를 내기 위해 IMX219 한 대가 두 트레이를 동시에 보는 구조로 전환했습니다.

```text
single 1280×720 frame
├─ left BEFORE ROI
└─ right AFTER ROI
```

각 트레이를 2×2 네 슬롯으로 분할하고 슬롯별로:

```text
A / B / C / EMPTY
```

를 판정했습니다.

### Lesson

해커톤에서는 이상적인 하드웨어 구조보다 **재현 가능한 fallback**을 빠르게 확보하는 것이 중요합니다.

---

## 6. HSV and tray stabilization

### Color mapping

```text
A = orange
B = light green
C = light blue
```

### Calibration strategy

- 최종 카메라 높이·각도와 조명에서 보정
- BEFORE와 AFTER를 별도 HSV 범위로 저장
- 각 슬롯 내부 margin을 제외하고 색 면적 ratio 계산
- morphology open/close로 작은 noise 제거
- 여러 프레임의 수량 mode를 사용해 안정화

### Why fixed slots

Contour count만 사용하면 상품이 붙었을 때 하나로 합쳐질 수 있습니다. 2×2 슬롯 점유 방식은 상품 위치가 고정된 시연 환경에서 훨씬 안정적이었습니다.

### Lesson

색 분류는 HSV 값만의 문제가 아니라 **카메라 위치, 조명, ROI, 점유율 threshold, 시간 안정화**의 조합입니다.

---

## 7. Dedicated RPi–Fusion Ethernet

학교 Wi-Fi와 별개로 Raspberry Pi와 Fusion PC를 직접 Ethernet으로 연결했습니다.

```text
Fusion Ethernet  10.77.0.1/24
RPi eth0         10.77.0.2/24
```

Ethernet에는 gateway와 DNS를 두지 않고 Wi-Fi가 인터넷 기본 경로를 유지하도록 구성했습니다.

Channels:

```text
RPi PUB 5562 → Fusion SUB
Fusion PUSH 5563 → RPi PULL
```

### Lesson

현장 네트워크의 DHCP·인증·혼잡을 피하려면 장치 간 control plane을 고정 유선망으로 분리하는 것이 효과적입니다.

---

## 8. Audio state integration

상황별 WAV를 미리 생성하여 RPi에 저장하고, 실행 중 TTS에 의존하지 않도록 했습니다.

```text
SYSTEM_READY
PLACE_BEFORE
SCAN_PRODUCT
SCAN_COMPLETED
TRAY_MISMATCH
SYSTEM_RESET
```

Fusion은 결제 완료와 reset을 5563으로 보내고, RPi는 자체 트레이 상태에 따라 scan/mismatch 안내를 재생합니다.

### Lesson

발표 환경에서는 온라인 TTS보다 **사전 생성된 deterministic media**가 안정적입니다.

---

## 9. Vision integration evolution

### Experimental assumption

개발 중 Fusion은 `zone_A_picks` 누적값이 0→1→2로 주기 송신된다고 가정해 증가분을 `REMOVE_CANDIDATE`로 변환했습니다.

### Final upstream semantics

도율님 최종 Vision upstream은 외부 5555에 다음 one-shot transition을 보냅니다.

```text
state=POS
state=EXIT
```

EXIT packet의 A/B/C가 최종 PICK 수량입니다.

### Required Fusion behavior

```text
POS packet
→ customer_id 기준 결제 세션 준비

EXIT packet
→ final picked vs cached paid 비교
```

### Emergency integration

초기 계획은 `5557 CAPTURE_EVIDENCE`였지만 최종 upstream에는 실제 WebUI Emergency `REP :5556`가 구현되었습니다.

```text
Fusion REQ {Emergency:true, customer_id}
→ Vision WebUI REP
→ customer entry JPEG lookup
→ red theft alert and image
```

### Lesson

통합 문서는 개발 중 가정이 아니라 **최종 producer의 wire protocol**을 기준으로 잠가야 합니다.

---

## 10. Unpaid and mismatch reasoning

고객별 최종 판정:

```text
picked  = Vision EXIT A/B/C
paid    = same customer POS payment
unpaid  = max(picked - paid, 0)
overpay = max(paid - picked, 0)
```

Results:

```text
NO_ITEMS
CLEARED
BYPASS_POS_NO_PAYMENT
NO_PAYMENT
PARTIAL_PAYMENT
OVERPAYMENT
```

Additional tray result:

```text
expected = POS payment
actual   = AFTER tray
missing  = max(expected - actual, 0)
extra    = max(actual - expected, 0)
```

### Alert actions

- Fusion dashboard alert
- Rider LED RED
- RPi mismatch WAV
- Vision WebUI Emergency customer snapshot
- JSONL event logging

---

## 11. Documentation and archive decisions

### Source ownership

Vision source was kept in its original repository rather than copied without history:

- [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv)

The integrated repository pins an archive commit and documents the protocol and checkout method.

### Large assets

Model weights and large media are not blindly committed. Reproduction requires:

- asset filename
- source and license
- SHA-256
- model class map
- Git LFS or external artifact link

### Public safety

The archive excludes:

- passwords and tokens
- school account credentials
- personal network settings
- generated logs and captures
- build products that cannot be traced to their source

---

## 12. What worked

- Real POS and Rider devices were connected to a central Python state machine.
- RPi tray counts and audio commands were exchanged over a dedicated Ethernet ZMQ link.
- Vision customer state reached Fusion over ROS2→ZMQ.
- Customer and Rider use cases were expressed as separate ledgers rather than one overloaded count.
- Hardware failures were handled with a working fallback instead of blocking the whole demonstration.

## 13. What should be improved next

- Durable delivery or ACK for one-shot Vision POS/EXIT packets
- transaction/order ID shared across Vision, POS and Fusion
- multi-customer concurrency in Fusion
- RETURN behavior and inventory increment
- evidence request integration directly in the final Fusion main loop
- model artifact registry and license documentation
- automated end-to-end integration test using replayed serial and ZMQ logs
- richer authenticated operator UI

---

## 14. Closing note

대회 수상 여부와 별개로, 이 프로젝트의 핵심 결과는 서로 다른 보드·운영체제·프로토콜을 실제 하나의 상태 흐름으로 연결하고, 실패한 하드웨어와 잘못된 의미 해석을 통합 과정에서 수정했다는 점입니다. 저장소는 결과 화면뿐 아니라 이 의사결정과 문제 해결 과정을 재현 가능한 팀 자산으로 남기기 위해 정리했습니다.
