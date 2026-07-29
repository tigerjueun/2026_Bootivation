
# Contributing

## 브랜치

- `main`: 검증된 아카이브
- `vision/*`: 도율님 ROS/모델 추가
- `fix/*`: 버그 수정
- `docs/*`: 문서 수정

## 커밋 예시

```text
feat(vision): add retail tracking ROS package
fix(fusion): debounce unpaid alert
firmware(rider): update calibrated servo angles
docs: add final demo runbook
```

## 대용량 파일

모델 가중치와 대형 영상은 Git LFS를 사용합니다.

```bash
git lfs install
git lfs track "*.pt" "*.onnx" "*.engine" "*.mp4"
git add .gitattributes
```

개인 IP, 비밀번호, 토큰, 학교 계정 정보는 커밋하지 않습니다.
