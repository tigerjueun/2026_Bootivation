# Evidence / Emergency Request

이 문서는 초기 설계의 `5557 PUSH/PULL CAPTURE_EVIDENCE` 계획을 보존하던 파일입니다. 도율님 Vision WebUI 최종 구현에서는 별도 `5557` 채널 대신 **ZMQ REQ/REP `5556` Emergency API**가 실제로 구현되었습니다.

최종 계약은 다음 문서를 사용합니다.

- [`EMERGENCY_ZMQ.md`](EMERGENCY_ZMQ.md)
- Upstream: [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv)
- Upstream guide: `ZMQ_EMERGENCY_RECEIVER_GUIDE.md`

## Final request

```json
{
  "Emergency": true,
  "customer_id": 100,
  "timestamp": 1784902700.2
}
```

```text
Fusion ZMQ REQ
→ tcp://VISION_PC_IP:5556
→ Vision WebUI ZMQ REP
→ Camera 1 entry JPEG lookup
→ response
→ WebSocket theft alert and customer image
```

## Final response

```json
{
  "ok": true,
  "customer_id": 100,
  "snapshot_available": true
}
```

## Deprecated draft

아래 초기안은 최종 프로토콜이 아니므로 새 코드에서 사용하지 않습니다.

```text
DEPRECATED: Fusion PUSH → Vision PULL :5557
DEPRECATED: {"command":"CAPTURE_EVIDENCE", ...}
```

Git 이력과 설계 변화를 설명하기 위해 파일명은 유지하지만, 실제 실행과 문서는 `5556 REQ/REP`를 기준으로 합니다.
