# ATMEGA128_POS_C UART → Fusion 통합

## 지원 프로토콜

패치는 기존 문자열과 새 CSV 프로토콜을 동시에 지원한다.

- 기존: `MODE:CUSTOMER`, `PAY:A`, `PAY_DONE`, `RESET`
- 신규: `USER,CUSTOMER`, `SESSION,START,ID=1`, `COUNT,...`, `PAY_DONE,USER=...`, `SESSION_RESET`

## 중복 계산 방지

신규 펌웨어는 완료 시 두 줄을 연속 전송한다.

```text
PAY_DONE
PAY_DONE,USER=CUSTOMER,A=1,B=2,C=1,TOTAL=4,SESSION=2
```

Fusion은 결제 묶음을 한 번만 증가시키고 상세 줄은 수량 검증·보정에 사용한다.

## 수동 POS RESET

`SESSION_RESET` 전에 입력된 PAY는 완료되지 않은 거래다. Fusion은 현재 POS 거래에서 입력된 수량을 고객 결제 장부 또는 Rider 선택 장부에서 되돌린다.

## Rider 입력 소스

설정 파일의 `rider.pick_source`로 선택한다.

```json
"rider": {
  "enabled": true,
  "port": "COM10",
  "baud": 9600,
  "timeout_sec": 0.2,
  "pick_source": "pos"
}
```

- `pos`: Rider의 `PAY:A/B/C`를 실제 픽업 입력으로 사용
- `vision`: `REMOVE_CANDIDATE:A/B/C`를 사용
- `both`: 둘 다 사용하므로 중복 이벤트 관리가 필요함

실물 통합에서는 `pos` 권장, 기존 수동 Rider 테스트 설정은 `vision` 유지.

## 테스트

```powershell
cd C:\Project\2026\Bootivation\Bootivation_v2\fusion_pc
py -m unittest .\tests\test_pos_uart_v2.py -v
```

샘플 로그 재생:

```powershell
py .\tools\replay_pos_uart_v2.py ..\samples\pos_uart_v2_sample.log --rider-pick-source pos
```

실물 POS만 연결:

```powershell
py .\main.py --config ..\config\pos_only.json
```

전체 통합 전 `config/system.json` 또는 별도 full 설정에서 POS 포트, Rider COM10, `pick_source: pos`를 확인한다.
