# Project Status

2026 SSG-SSAC Bootivation 해커톤 결과물을 재현 가능한 형태로 정리한 아카이브입니다. 수상에는 이르지 못했지만, POS, Rider 안내 장치, Raspberry Pi 계산 트레이, ROS 2 Vision, Fusion 상태머신을 실제 네트워크와 직렬 통신으로 연결했습니다.

## Completed archive

- [x] Fusion 상태머신, 고객·Rider 장부, 운영 대시보드
- [x] ATmega128 POS 모듈형 C 소스, 핀맵, UART 계약
- [x] Arduino Rider 최종 보정 펌웨어와 배선 문서
- [x] RPi 단일 카메라 2트레이 HSV/ZMQ/오디오
- [x] Vision upstream 저장소와 고정 커밋 연결
- [x] Vision customer-state 5555 최종 POS/EXIT 계약
- [x] Vision WebUI Emergency 5556 REQ/REP 계약
- [x] RPi 5562/5563 계약
- [x] 고객 정상·부분 결제·미결제 시나리오
- [x] 배달기사 주문·Vision 제거·POS 확인 3중 검증
- [x] 아키텍처, 런북, 개발 회고, 팀 역할 문서
- [x] App Inventor 점검 앱의 용도와 제한 기록

## Vision source

Vision 전체 원본은 아래 저장소에서 관리합니다.

- [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv)
- Archive commit: [`3d9225e`](https://github.com/Kuz-DX/ssg-ssac-cctv/commit/3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef)

통합 저장소는 원본 commit history를 보존하기 위해 Vision 소스를 복사하지 않고 upstream 링크와 통신 계약을 관리합니다.

## Remaining optional artifacts

- [ ] 팀 YOLO 가중치의 보관 위치·라이선스·SHA-256 manifest 확정
- [ ] 최종 데모 사진·영상 추가
- [ ] App Inventor `.aia` 원본의 공개 여부 결정
- [ ] WAV 파일의 공개 재배포 가능 여부 확인
- [ ] 로컬 종료 시점 working tree와 공개 archive 최종 diff
- [ ] 선택적 GitHub release/tag 생성

## Known final limitations

- Vision 5555는 고객별 POS/EXIT를 한 번씩 발행하는 PUB/SUB이므로 전달 보장이 없습니다.
- 상품 RETURN과 수량 감소는 Vision 최종 범위에 포함되지 않았습니다.
- Fusion은 해커톤 단일 시연 중심이며 다중 고객·다중 결제 transaction correlation은 추가 설계가 필요합니다.
- RPi 최종 시연은 CSI 문제로 카메라 한 대가 두 트레이를 동시에 보는 fallback 구조입니다.
- 모델 가중치는 public Git에 포함되어 있지 않습니다.
- ZMQ 채널은 인증·암호화가 없어 신뢰 가능한 내부망을 전제로 합니다.
