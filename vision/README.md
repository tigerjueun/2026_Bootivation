# Vision / ROS 2 Module

Bootivation의 Vision 파트는 도율님이 개발한 별도 upstream 저장소에서 관리됩니다.

- Repository: [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv)
- Archive commit: [`3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef`](https://github.com/Kuz-DX/ssg-ssac-cctv/commit/3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef)
- Environment: Ubuntu 22.04, ROS 2 Humble, Python 3.10

이 통합 저장소는 Vision 소스의 복제본을 임의로 다시 작성하지 않고, upstream 링크·고정 커밋·통신 계약·실행 문서를 보존합니다. 이렇게 해야 도율님의 원본 커밋 이력과 기여가 명확하게 남습니다.

## What the upstream contains

```text
ssg-ssac-cctv/
├── perception/
│   ├── README.md
│   ├── requirements.txt
│   ├── weights/                       # runtime model location
│   └── src/retail_perception/
│       ├── config/pipeline.yaml
│       ├── launch/retail_pipeline.launch.py
│       ├── retail_perception/
│       │   ├── perception_node.py
│       │   ├── tracker.py
│       │   ├── identity.py
│       │   ├── pick_fsm.py
│       │   ├── customer_lifecycle.py
│       │   ├── customer_state_filter.py
│       │   ├── tracking_fsm_node.py
│       │   └── zmq_transmitter_node.py
│       └── test/
├── webUI/
│   ├── run_model_test.sh
│   └── server.py
├── ZMQ_CUSTOMER_RECEIVER_GUIDE.md
└── ZMQ_EMERGENCY_RECEIVER_GUIDE.md
```

## Core functions

- 두 압축 카메라 토픽의 저지연 구독
- 사람·손·상품 A/B/C 통합 YOLO 검출
- 상품·손 보조 모델과 IoU 기반 deduplication
- 카메라별 ByteTrack 방식 로컬 추적
- OpenVINO Person Re-ID / HSV fallback
- Homography를 이용한 공통 바닥 좌표 매칭
- 입장·매장·퇴장 lifecycle과 전역 `customer_id`
- 카메라별 entrance, kiosk, A/B/C polygon ROI
- 손·상품·사람 이동을 이용한 multi-frame PICK FSM
- WebUI 추적 시각화와 ROI 좌표 도구
- 고객 POS/EXIT 상태 ZMQ PUB 5555
- 절도 의심 고객 Emergency ZMQ REP 5556

## Clone the pinned version

```bash
git clone https://github.com/Kuz-DX/ssg-ssac-cctv.git ssg-ssac-cctv
cd ssg-ssac-cctv
git checkout 3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef
```

Or keep the latest upstream:

```bash
git clone https://github.com/Kuz-DX/ssg-ssac-cctv.git ssg-ssac-cctv
```

## Documents in this repository

- [`UPSTREAM.md`](UPSTREAM.md): upstream commit, setup and model availability
- [`contracts/RETAIL_ZMQ.md`](contracts/RETAIL_ZMQ.md): customer POS/EXIT state contract
- [`contracts/EMERGENCY_ZMQ.md`](contracts/EMERGENCY_ZMQ.md): Emergency request/response contract
- [`../docs/VISION_INTEGRATION.md`](../docs/VISION_INTEGRATION.md): full architecture and model details
- [`mock/`](mock/): communication tests; not the production ROS pipeline

## Important protocol note

The final upstream transmitter publishes customer states only when a customer first reaches the POS and when the visit exits. It does **not** periodically publish every pick frame. Fusion should therefore store the POS packet by `customer_id`, accept the EXIT packet as the final pick count and start the subscriber before the Vision event occurs.

## Model files

The upstream source references YOLO and Re-ID weights, but `.pt` files are excluded from normal Git tracking. See [`../models/README.md`](../models/README.md) before trying to reproduce the pipeline.
