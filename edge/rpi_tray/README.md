# Bootivation 단일 카메라 2트레이 패키지

IMX219 한 대로 계산 전(BEFORE)과 계산 후(AFTER) 트레이를 한 화면에 담고,
각 트레이를 2x2 네 슬롯으로 나눠 A/B/C/EMPTY를 판정합니다.

## 권장 물리 배치

카메라 화면 기준:

```text
┌──────────────┬──────────────┐
│ BEFORE 트레이 │ AFTER 트레이  │
│   2 x 2      │   2 x 2      │
└──────────────┴──────────────┘
```

## 설치

```bash
cd ~/Bootivation
unzip -o Bootivation_RPi_SingleCam_2Tray_v1.zip
mv Bootivation_RPi_SingleCam_2Tray_v1 rpi_tray_single
cd ~/Bootivation/rpi_tray_single
```

## 1. ROI 위치 조정

```bash
python3 single_tray_position.py --layout 2x2
```

키:

```text
B = BEFORE ROI 선택
A = AFTER ROI 선택
L = 2x2 / 1x4
S = 저장
Q = 종료
```

## 2. HSV 보정

```bash
python3 single_hsv_calibrator.py
```

키:

```text
B = BEFORE
A = AFTER
1 = 상품 A(주황)
2 = 상품 B(초록)
3 = 상품 C(파랑)
원본 클릭 = 자동 샘플
S = 저장
Q = 종료
```

## 3. 수량 판정

```bash
python3 single_slot_counter.py
```

로그:

```text
~/Bootivation/rpi_tray_single/logs/slot_counts.jsonl
```
