
# Hardware summary

## POS

ATmega128, LCD, FND, 조이스틱, 초음파, IR, 터치 A/B/C/DONE로 구성됩니다. 최신 핀 기준은 `firmware/atmega128_pos/docs/PIN_MAP.txt`와 실제 소스를 우선합니다.

## Rider

Arduino UNO + HC-06 + 서보 + 3색 LED. 서보 각도는 A=85°, B=45°, C=0°, HOME=150°입니다.

## RPi tray

Raspberry Pi 5 + IMX219. 최종 시연에서는 카메라 한 대가 계산 전/후 두 트레이를 동시에 보고 각각 2×2 슬롯을 분류했습니다. 상품 매핑은 A=주황, B=연두, C=하늘색입니다.
