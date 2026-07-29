
# Test scenarios

1. Rider 정상 수집: order A1/B1/C1 → Vision A/B/C 증가 → HOME/GREEN → POS Rider A/B/C DONE.
2. Rider 오픽업: 주문에 없는 상품 증가 → RED.
3. 고객 정상 결제: Vision 픽업량과 POS 결제량 일치 → 정상 퇴장.
4. 부분 결제: picked-paid 차이를 상품별 계산 → 경보음/RED/UI.
5. 완전 미결제: 상품 보유 후 EXIT, 결제 0 → 긴급 경보.
6. 트레이 불일치: POS expected와 AFTER 불일치 → `tray_mismatch.wav`.
7. 장치 단절: Vision/RPi 스트림 stale → UI 장치 경고.
