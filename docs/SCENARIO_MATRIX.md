# Bootivation 고급 이벤트·행동 시나리오 매트릭스

## 1. 고객 계산 시나리오

| 상황 | 계산 | 결과 코드 | 자동 행동 | UI |
|---|---|---|---|---|
| 상품 없이 퇴장 | picked=0 | `NO_ITEMS` | 경보 없음 | 정보 기록 |
| 픽업=결제 | picked-paid=0 | `CLEARED` | 정상 통과 | 성공 표시 |
| POS 미경유 + 미결제 | paid=0, picked>0, `was_at_kiosk=false` | `BYPASS_POS_NO_PAYMENT` | RPi 경고음 + Rider RED | 긴급 경보/점멸 |
| POS 경유했으나 결제 없음 | paid=0, picked>0 | `NO_PAYMENT` | RPi 경고음 + Rider RED | 긴급 경보 |
| 일부만 결제 | `unpaid=max(picked-paid,0)` > 0 | `PARTIAL_PAYMENT` | 미결제 품목별 경고 | A/B/C 차이 표시 |
| 픽업보다 결제량이 많음 | `overpaid=max(paid-picked,0)` > 0 | `OVERPAYMENT` | 차단하지 않음 | 경고 표시 |
| 추적 취소, 픽업 없음 | picked=0 | `NO_ITEMS` | 무시 | 타임라인만 기록 |

## 2. 배달기사 시나리오

| 상황 | 계산 | 자동 행동 | UI |
|---|---|---|---|
| 주문 등록 | `order_items` 설정 | BLUE + 첫 상품 서보 | 주문 수량/진행률 |
| 정상 수집 | `collected <= order` | 다음 상품 서보 | A/B/C 수집 수량 |
| 잘못된/초과 상품 | `max(collected-order,0)>0` | RED | `RIDER_PICK_ERROR` 긴급 경보 |
| 수집 완료 | `order == collected` | HOME + GREEN | 100%, POS 확인 대기 |
| POS 확인 부족 | `checked < order` | 기존 StateManager 결과 반영 | 누락 수량 표시 |
| POS 확인 초과/불일치 | `checked != order` | RED | 긴급 경보 |
| 최종 일치 | order=collected=checked | GREEN | 완료 이력 |

## 3. 계산 트레이 시나리오

| 상황 | 계산 | 결과 | 행동 |
|---|---|---|---|
| 결제 전 상품 감지 | BEFORE>0 | 스캔 중 | 안내 음성 |
| 결제 확정 | expected=POS 결제량 | 이동 대기 | 완료 음성/AFTER 이동 |
| AFTER 정확히 일치 | after=expected, before=0 | `TRAY_COMPLETE` | 정상 완료 |
| 종류/수량 불일치 | after!=expected, before=0 | `TRAY_MISMATCH` | 경고음 + UI 긴급 경보 |
| 누락 품목 | `missing=max(expected-after,0)` | 불일치 상세 | A/B/C 누락 표시 |
| 초과 품목 | `extra=max(after-expected,0)` | 불일치 상세 | A/B/C 초과 표시 |

## 4. 장치 상태 시나리오

| 장치 | 감시 | 경보 |
|---|---|---|
| Vision | `retail` 메시지 최종 수신 시각 | 4초 이상 중단 시 `DEVICE_STALE:vision` |
| RPi | `TRAY_COUNT` 최종 수신 시각 | 4초 이상 중단 시 `DEVICE_STALE:rpi` |
| POS | 직렬 이벤트 수신 및 COM 시작 | 연결 실패/이벤트 상태 표시 |
| Rider | COM10 open 성공 여부 | 실패 시 `DEVICE_OFFLINE:rider` |

## 5. 운영자 UI 행동

- 활성 경보 확인/전체 확인
- 해제된 경보 정리
- 전체 세션 초기화
- RPi 세션 초기화
- 상황별 WAV 수동 재생
- Rider RED/GREEN/OFF
- 서보 HOME
- 장치 온라인 상태, 고객 수량, 배달기사 진행률, 트레이 차이, 타임라인 확인

## 6. 현재 의도적으로 제한한 범위

- Fusion 상태머신이 단일 세션이라 Vision도 최초 활성 고객 한 명을 추적함
- 고객 여러 명 동시 결제 상관관계는 데이터베이스/주문 ID가 추가되어야 안전하게 확장 가능
- 웹 UI는 로컬 운영용이며 인증 기능은 없음. 기본 `127.0.0.1`에서만 열림
