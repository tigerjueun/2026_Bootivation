# Legacy tests

`test_pos_uart_v2_legacy.py`는 POS가 Rider 픽업량을 직접 누적하던 이전 의미론을 검증합니다.
최종 저장소는 주문·Vision 제거·POS 확인을 분리하는 three-way 상태머신을 사용하므로 기본 테스트 대상에서 제외합니다.
