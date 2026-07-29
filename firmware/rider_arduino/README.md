# Rider Arduino

Arduino UNO + HC-06 + 서보 + 3색 LED 상품 위치 안내 장치.

핀: Servo D9, HC-06 D10/D11, Blue D3, Red D4, Green D5.
각도: A=85°, B=45°, C=0°, HOME=150°.
명령: `PING`, `GET_STATUS`, `SERVO:*`, `LED:*`, `RESET`.
서보는 외부 5–6V와 Arduino 공통 GND를 사용합니다.
