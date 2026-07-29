# ATmega128 POS 키오스크 C 프로젝트

ASM 기반 POS를 모듈형 AVR-GCC C로 재구성했습니다.

## 흐름
1. 초음파 사람 접근
2. 조이스틱 CUSTOMER/RIDER 선택
3. IR 상품 감지
4. PE4~PE6 A/B/C, PE7 DONE
5. UART0 57600으로 세션·수량·완료 전송

빌드: `build_hex.bat` 또는 `make`. 최신 핀맵과 UART 계약은 `docs/`를 참고하세요.
