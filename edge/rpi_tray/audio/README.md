
# Audio prompts

프로젝트에서 실제 사용한 WAV 안내 파일입니다.

| Event | File | 안내 |
|---|---|---|
| SYSTEM_READY | `system_ready.wav` | 어서오세요. 쓱싹입니다. |
| PLACE_BEFORE | `place_before.wav` | 상품을 계산 전 트레이에 올려 주세요. |
| SCAN_PRODUCT | `scan_product.wav` | 상품을 스캔해주세요. |
| SCAN_COMPLETED | `scan_completed.wav` | 모든 상품이 결제되었습니다. |
| TRAY_MISMATCH | `tray_mismatch.wav` | 상품 수량이 일치하지 않습니다. 다시 확인해 주세요. |
| SYSTEM_RESET | `system_reset.wav` | 처음부터 다시 시작합니다. |

재생은 PipeWire의 `pw-play`를 우선 사용합니다.
