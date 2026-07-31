# Team & Contributions

Bootivation은 짧은 해커톤 기간 동안 기획, 비전, 임베디드 POS, 배달기사 안내 장치, Raspberry Pi 계산 트레이, 중앙 Fusion을 병렬 개발한 프로젝트입니다. 아래 표는 각 팀원의 **주요 담당 영역**을 정리한 것이며, 실제 현장에서는 전원이 조립·시험·통합·발표에 함께 참여했습니다.

| 팀원 | GitHub | 주요 역할 | 담당 결과물 |
|---|---|---|---|
| **박주은** | [@tigerjueun](https://github.com/tigerjueun) | 시스템 아키텍처, Fusion PC, 전체 통신·통합, RPi 트레이·음성, Rider 펌웨어 보정, GitHub 아카이빙 | Python 상태머신, POS/Rider/RPi/Vision 연동, ZMQ·Serial, 미결제·트레이·Rider 검증 로직, 실행 문서 |
| **혜은** | 추후 연결 | ATmega128 POS | 기존 ASM 동작 분석, C 모듈화, 초음파·IR·터치·조이스틱, LCD/FND UI, POS 실물 회로 |
| **진호** | 추후 연결 | Rider Arduino·모바일 프로토타입 | HC-06, 서보 화살표, 3색 LED, 외부전원·납땜, App Inventor 장치 점검 앱 |
| **도율** | [@Kuz-DX](https://github.com/Kuz-DX) | Ubuntu ROS 2 Vision·CCTV WebUI | 듀얼 카메라 YOLO, ByteTrack, 전역 고객 ID, Re-ID·Homography, PICK FSM, ROI 도구, ZMQ 고객 상태·Emergency 경보 |
| **시은** | 추후 연결 | PM·서비스 기획·발표 | 서비스 시나리오, 기능 우선순위, 일정·역할 조율, 발표 구조와 현장 운영 |

## Repository ownership

- 통합 저장소와 공통 계약: [tigerjueun/2026_Bootivation](https://github.com/tigerjueun/2026_Bootivation)
- Vision 원본 소스와 커밋 이력: [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv)
- Vision 아카이브 기준: [`3d9225e`](https://github.com/Kuz-DX/ssg-ssac-cctv/commit/3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef)

## Contribution guideline

저장소 정리는 박주은이 원본 `main`에서 관리합니다. 팀원은 결과물을 본인 계정에 보관하려면 GitHub의 **Fork** 기능을 사용할 수 있으며, 수정 사항이 있다면 별도 브랜치 또는 Pull Request로 남기는 방식을 권장합니다.
