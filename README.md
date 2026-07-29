
# Bootivation

무인매장 환경에서 고객·배달기사의 상품 수집, 결제, 트레이 이동을 여러 엣지 장치가 협력해 검증하는 해커톤 프로젝트입니다.

> 2026 SSG-SSAC 해커톤 아카이브. 대회 결과와 별개로 실제 통합 과정, 펌웨어, 상태머신, 프로토콜을 재현 가능하게 남기는 것을 목표로 합니다.

## 핵심 기능

- Ubuntu ROS2 Vision에서 고객 추적과 A/B/C 누적 픽업 수량 송신
- ATmega128 POS에서 고객·라이더 상품 확인 및 결제 장부 송신
- Arduino/HC-06로 배달기사 상품 위치 화살표와 LED 안내
- Raspberry Pi 카메라에서 계산 전/후 2×2 트레이 슬롯 HSV 분류
- Fusion PC에서 주문·픽업·POS·트레이 정보를 결합해 정상/오류/미결제를 판정
- WAV 음성 안내와 로컬 운영 대시보드

## 저장소 구조

```text
fusion_pc/             Fusion 상태머신·통신·운영 UI
firmware/atmega128_pos ATmega128 POS C 소스
firmware/rider_arduino Arduino/HC-06/서보/LED
edge/rpi_tray          RPi HSV 트레이·오디오·ZMQ
vision/                ROS Vision 계약·수동 mock·인수 예정 폴더
apps/app_inventor      하드웨어 점검용 앱
shared/                JSON schema와 공통 계약
docs/                  구조·실행·시험 문서
models/                최종 모델 추가 예정
```

## 네트워크

```text
Vision PUB 5555 → Fusion
RPi PUB 5562 → Fusion
Fusion PUSH 5563 → RPi
Fusion serial COM5 →/← POS
Fusion serial COM10 → Rider
Fusion HTTP 8088 → 운영 대시보드
```

## 빠른 시작

1. `fusion_pc/config/system.example.json`을 `system.json`으로 복사하고 포트/IP를 수정합니다.
2. RPi에서 `scripts/rpi/run_tray.sh`를 실행합니다.
3. Vision PC에서 ROS 추적 노드와 5555 transmitter를 실행합니다.
4. Windows에서 `scripts/windows/run_fusion.ps1`을 실행합니다.
5. `http://127.0.0.1:8088`에서 상태를 확인합니다.

자세한 순서는 [`docs/RUNBOOK.md`](docs/RUNBOOK.md)를 참고하세요.

## 현재 상태

도율님의 최종 Vision/ROS 코드와 모델은 아직 전달 전입니다. 인터페이스와 폴더는 미리 준비되어 있으며, 수령 후 `vision/doyul_module/`과 `models/`에 추가합니다.

## 팀

역할은 [`TEAM.md`](TEAM.md)에 정리했습니다. 팀원 GitHub 사용자명을 받으면 collaborator로 초대하고 갱신합니다.
