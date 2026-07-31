# Doyul Vision Module Handoff

도율님의 최종 ROS 2 Vision 코드 전달은 별도 upstream 저장소 공개로 완료되었습니다.

- Repository: [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv)
- Archive commit: [`3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef`](https://github.com/Kuz-DX/ssg-ssac-cctv/commit/3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef)
- Integration guide: [`../UPSTREAM.md`](../UPSTREAM.md)
- Technical summary: [`../../docs/VISION_INTEGRATION.md`](../../docs/VISION_INTEGRATION.md)

## Handoff status

```text
[x] ROS 2 package and Python sources
[x] launch/config/pipeline YAML
[x] requirements and execution guide
[x] customer-state ZMQ 5555 guide
[x] Emergency ZMQ 5556 guide
[x] CCTV WebUI and ROI tool
[x] final source commit pinned
[ ] YOLO weight files archived with redistribution metadata
[ ] final demonstration media added to integrated repository
```

## Why the source is not copied here

원본 저장소를 upstream으로 연결하면:

- 도율님의 commit history와 authorship가 보존됩니다.
- 동일 소스가 두 저장소에서 서로 달라지는 문제를 줄일 수 있습니다.
- 모델과 Vision 전용 이슈는 원본 저장소에서 이어서 관리할 수 있습니다.
- 통합 저장소는 공통 프로토콜, Fusion, POS, Rider, RPi와 전체 문서에 집중할 수 있습니다.

전체 소스를 함께 내려받는 명령은 [`../UPSTREAM.md`](../UPSTREAM.md)를 참고하세요.
