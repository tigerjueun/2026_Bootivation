# Vision Upstream Reference

## Canonical repository

- Owner: [Kuz-DX](https://github.com/Kuz-DX)
- Repository: [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv)
- Default branch: `main`
- Bootivation archive commit: [`3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef`](https://github.com/Kuz-DX/ssg-ssac-cctv/commit/3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef)
- Commit message: `Final Code`

Vision 전체 소스는 기여자의 커밋 이력과 원본 저장소를 보존하기 위해 이 통합 저장소에 복사·재작성하지 않고 upstream으로 연결합니다.

## Checkout the archived version

```bash
git clone https://github.com/Kuz-DX/ssg-ssac-cctv.git
cd ssg-ssac-cctv
git checkout 3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef
```

통합 저장소 내부에 배치하려면:

```bash
git clone https://github.com/Kuz-DX/ssg-ssac-cctv.git \
  vision/ssg-ssac-cctv

git -C vision/ssg-ssac-cctv checkout \
  3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef
```

## Optional Git submodule workflow

팀이 두 저장소를 항상 함께 관리하기로 합의했다면 로컬에서 submodule로 연결할 수 있습니다.

```bash
git submodule add \
  https://github.com/Kuz-DX/ssg-ssac-cctv.git \
  vision/ssg-ssac-cctv

git -C vision/ssg-ssac-cctv checkout \
  3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef

git add .gitmodules vision/ssg-ssac-cctv
git commit -m "chore(vision): link pinned upstream repository"
```

이 아카이브에서는 외부 저장소를 강제로 vendoring하거나 submodule로 고정하지 않고, 문서 링크를 기본 방식으로 사용합니다.

## Upstream contents

```text
perception/
├── README.md
├── requirements.txt
├── weights/
└── src/retail_perception/
    ├── config/pipeline.yaml
    ├── launch/retail_pipeline.launch.py
    ├── retail_perception/
    │   ├── perception_node.py
    │   ├── tracker.py
    │   ├── identity.py
    │   ├── pick_fsm.py
    │   ├── customer_lifecycle.py
    │   ├── customer_state_filter.py
    │   ├── tracking_fsm_node.py
    │   └── zmq_transmitter_node.py
    └── test/

webUI/
├── run_model_test.sh
└── server.py

ZMQ_CUSTOMER_RECEIVER_GUIDE.md
ZMQ_EMERGENCY_RECEIVER_GUIDE.md
```

## Model availability

Upstream `.gitignore` excludes `*.pt`, so cloning the source does not guarantee that all YOLO weights are present. The source and configuration reference the following runtime assets:

```text
perception/weights/retail_best1.pt
perception/weights/box1.pt
perception/weights/hand_1(epo100).pt
perception/weights/person-reidentification-retail-0288.xml
perception/weights/person-reidentification-retail-0288.bin
```

Before reproducing the system, obtain the weights from the original team artifact storage and follow [`../models/README.md`](../models/README.md).

## Attribution

- Vision/ROS2/CCTV WebUI development: [Kuz-DX](https://github.com/Kuz-DX)
- Cross-device Fusion, embedded systems and archive integration: [tigerjueun](https://github.com/tigerjueun)

When reusing or publishing the Vision code, preserve the upstream repository link, commit attribution and licenses of the model weights and third-party components.
