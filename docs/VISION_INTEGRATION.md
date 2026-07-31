# Vision / ROS 2 Integration

Bootivation Vision 파트는 [Kuz-DX/ssg-ssac-cctv](https://github.com/Kuz-DX/ssg-ssac-cctv)에 구현되어 있습니다. 이 문서는 upstream의 최종 코드와 Bootivation Fusion 사이의 경계를 설명합니다.

- Archive commit: [`3d9225e`](https://github.com/Kuz-DX/ssg-ssac-cctv/commit/3d9225ebf47c9cbe7a231fe56d4bd2244c4696ef)
- OS: Ubuntu 22.04
- Middleware: ROS 2 Humble
- Runtime: Python 3.10
- Vision WebUI: HTTP/WebSocket `8080`
- Customer state: ZMQ PUB `5555`
- Emergency receiver: ZMQ REP `5556`

---

## 1. Pipeline overview

```mermaid
flowchart LR
    CAM1[/camera1/image_raw/compressed]
    CAM2[/camera2/image_raw/compressed]
    P[perception_node]
    DET[/perception/detections]
    T[tracking_fsm_node]
    STATE[/retail/customer_state]
    VIEW[/perception/tracked_detections]
    Z[zmq_transmitter_node]
    F[Fusion PC]
    WEB[CCTV WebUI]

    CAM1 --> P
    CAM2 --> P
    P --> DET --> T
    T --> STATE --> Z -->|retail JSON :5555| F
    T --> VIEW --> WEB
    F -->|Emergency REQ :5556| WEB
```

| Component | Input | Output | Responsibility |
|---|---|---|---|
| external camera nodes | USB camera | camera1/2 compressed topics | camera acquisition |
| `perception_node` | compressed JPEG | detection JSON | YOLO inference, class normalization, person descriptor |
| camera-local trackers | detections | local track ID | per-camera object continuity |
| global identity layer | local person tracks | `customer_id` | cross-camera customer association |
| `tracking_fsm_node` | tracks | customer and UI states | lifecycle, ROI, PICK, kiosk, exit |
| `zmq_transmitter_node` | `/retail/customer_state` | `retail {JSON}` | external customer-state delivery |
| WebUI server | tracked detections | browser view | CCTV, ID labels, ROI tool, Emergency alert |

The image and detection paths use low-latency ROS 2 settings such as `BEST_EFFORT`, `KEEP_LAST`, depth 1. Compressed JPEG is decoded directly with OpenCV so queued old frames do not accumulate through a bridge layer.

---

## 2. Detection models and class mapping

### Integrated model

```text
weights/retail_best1.pt
```

Model class order documented by the upstream:

| Model class ID | Model label | Internal pipeline class |
|---:|---|---|
| 0 | A | `product_A` / internal ID 2 |
| 1 | B | `product_B` / internal ID 3 |
| 2 | C | `product_C` / internal ID 4 |
| 3 | hand | `hand` / internal ID 1 |
| 4 | person | `person` / internal ID 0 |

Relevant parameters:

```yaml
integrated_model_path: weights/retail_best1.pt
integrated_person_class_ids: [4]
integrated_hand_class_ids: [3]
integrated_product_a_class_ids: [0]
integrated_product_b_class_ids: [1]
integrated_product_c_class_ids: [2]
integrated_confidence: 0.25
```

### Auxiliary product model

```text
weights/box1.pt
```

Class order:

```text
A=0, B=1, C=2
```

The upstream merges integrated-model and product-model boxes and keeps the higher-confidence box when same-class IoU exceeds the configured deduplication threshold.

Relevant settings:

```yaml
product_confidence: 0.15
product_dedup_iou_threshold: 0.4
product_max_frame_area_ratio: 0.08
product_reject_frame_border: true
product_frame_border_margin_px: 3.0
```

These reject auxiliary product detections that cover too much of the frame or touch the image border, reducing cases where a wall or whole person is classified as a product.

### Hand and person filtering

The final configuration also refers to a dedicated hand model and applies hand deduplication. Nested person boxes may be suppressed when a small person box overlaps a larger one above a configured ratio.

```yaml
hand_model_path: weights/hand_1(epo100).pt
hand_confidence: 0.15
hand_dedup_iou_threshold: 0.5
suppress_nested_person_boxes: true
nested_person_overlap_threshold: 0.65
person_dedup_iou_threshold: 0.5
```

All model files must be obtained separately; see [`models/README.md`](../models/README.md).

---

## 3. Local tracking and global customer identity

### Camera-local tracking

Each camera has an independent ByteTrack-style tracker. Local tracking remains separate because image coordinates and observation angles differ by camera.

The tracker stores:

```text
local_track_id
bbox history
confidence
velocity / movement history
class
camera_id
```

### Cross-camera global ID

The global identity layer maps local person tracks to a shared `customer_id` using a combination of:

- appearance descriptor similarity
- OpenVINO Person Re-ID when configured
- HSV histogram fallback when Re-ID is unavailable
- optional common-ground coordinates from camera homography
- timestamp synchronization
- same-camera reacquisition rules

The configured Re-ID model is:

```text
person-reidentification-retail-0288.xml
person-reidentification-retail-0288.bin
```

The final pipeline contains calibrated 3×3 homography values for both cameras. Person image anchors are projected to a shared floor coordinate system, which supplements appearance matching when front/rear views differ.

---

## 4. Entrance, kiosk and zone ROI

The final upstream uses camera-specific polygon ROI for:

```text
camera1 entrance
camera1 kiosk
camera1 A / B / C
camera2 entrance
camera2 kiosk
camera2 A / B / C
```

A physical area must be calibrated independently in each camera because its projection differs.

### WebUI ROI coordinate tool

The Vision WebUI provides an ROI tool that:

1. selects a camera and region type
2. lets the operator click polygon vertices on the displayed video
3. converts screen coordinates back to source-frame coordinates
4. supports undo and copy
5. outputs YAML-style coordinates for `pipeline.yaml`

Example:

```yaml
camera1_zone_a_roi:
  [120.0, 80.0, 610.0, 95.0, 580.0, 690.0, 90.0, 650.0]
```

The final configuration enables both entrance/kiosk gating and A/B/C zone gating.

---

## 5. Customer lifecycle

The lifecycle layer handles more than raw object tracking.

```text
entering → inside → exiting → released
```

### Entry

A new global customer is not created merely because a person appears anywhere. The entrance camera's person anchor must pass through the entrance polygon in the configured direction for enough frames and displacement.

### Inside

After the entrance transition, the customer remains active across cameras while local IDs may change or temporarily disappear.

### Kiosk

A customer is marked at the POS when person/ROI overlap satisfies the camera-specific kiosk rules. The external customer-state filter emits a one-shot `state=POS` packet.

### Exit

The final code combines entrance lifecycle, disappearance handling and directional exit logic. On release it emits a final `state=EXIT`, `active=false` packet containing the customer's final A/B/C PICK counts.

---

## 6. PICK behavior FSM

PICK is not determined from a single overlap frame.

### Primary hand-product path

The system examines:

- hand/product overlap or edge distance
- object movement across multiple frames
- hand/product direction agreement
- cumulative product displacement
- customer association
- product zone of origin

### Product-motion fallback

When hand detection is missing, a product can still be confirmed as picked when it:

- starts in the matching A/B/C ROI
- moves toward the person over multiple frames
- passes minimum movement and distance-change thresholds

### Zone-approach fallback

The upstream also stores recent customer overlap with A/B/C zones. If a product becomes visible only after leaving the shelf, recent zone approach plus product movement near that customer can support a PICK decision.

### Deduplication

The implementation prevents duplicate count increases from:

- the same local product track
- multiple cameras observing the same customer/product action
- product-track fragmentation shortly after a count

The final project scope counts PICK increases. RETURN detection and quantity decrement are not included.

---

## 7. ZMQ customer-state integration

The final upstream sends only one-shot customer transitions on `5555`:

```text
state=POS
state=EXIT
```

Detailed contract: [`vision/contracts/RETAIL_ZMQ.md`](../vision/contracts/RETAIL_ZMQ.md)

Fusion behavior:

```text
POS packet
→ cache customer_id and current PICK snapshot
→ associate subsequent CUSTOMER POS payment

EXIT packet
→ use final zone_A/B/C_picks
→ compare with cached payment
→ clear, partial-payment or no-payment result
```

This differs from the earlier experimental integration that converted every cumulative-count increase to a `REMOVE_CANDIDATE` event. The archived Fusion adapter should follow the final POS/EXIT semantics when reproducing the final upstream.

---

## 8. Emergency screenshot integration

The Vision WebUI includes a ZMQ REP receiver on `5556`. Fusion sends:

```json
{
  "Emergency": true,
  "customer_id": 100
}
```

The WebUI:

```text
validates request
→ searches Camera 1 entry JPEG by customer_id
→ replies with snapshot_available
→ sends WebSocket emergency event
→ shows theft alert and entry image
```

Default captures:

```text
/tmp/bootivation_customer_captures
customer_100_entry_<timestamp_ms>.jpg
```

Detailed contract: [`vision/contracts/EMERGENCY_ZMQ.md`](../vision/contracts/EMERGENCY_ZMQ.md)

---

## 9. Build and run

```bash
cd /home/kuzdx/bootivation
sudo apt install ros-humble-usb-cam ros-humble-compressed-image-transport
python3 -m pip install -r perception/requirements.txt
source /opt/ros/humble/setup.bash
cd perception
colcon build --symlink-install --packages-select retail_perception
source install/setup.bash
```

Run the model/WebUI path:

```bash
cd /home/kuzdx/bootivation
./webUI/run_model_test.sh
```

Run the final 5555 transmitter in a separate terminal:

```bash
cd /home/kuzdx/bootivation
source /opt/ros/humble/setup.bash

PYTHONPATH="$PWD/perception/src/retail_perception${PYTHONPATH:+:$PYTHONPATH}" \
python3 -c 'from retail_perception.zmq_transmitter_node import main; main()' \
  --ros-args \
  --params-file "$PWD/perception/src/retail_perception/config/pipeline.yaml"
```

Expected:

```text
Publishing customer states on tcp://*:5555
ZMQ emergency receiver: tcp://*:5556
```

---

## 10. Tests and calibration

The upstream includes pure-logic tests for geometry, tracking, identity, lifecycle, PICK logic and state filtering. Runtime reproduction additionally requires:

- two camera topics at the expected resolution
- final polygon ROI
- final homography
- available model weights
- correct class-ID mapping
- Fusion subscriber running before one-shot POS/EXIT events

Useful checks:

```bash
ros2 topic hz /camera1/image_raw/compressed
ros2 topic hz /camera2/image_raw/compressed
ros2 topic echo /retail/customer_state --once
ss -ltnp | grep -E ':5555|:5556'
```

---

## 11. Known limits

- Final external 5555 messages are one-shot and not durable.
- Simultaneous multi-customer correlation remains more complex than a single demonstration session.
- Homography and ROI values are installation-specific.
- Re-ID can still confuse visually similar customers without strong spatial calibration.
- PICK counting does not implement RETURN decrement.
- Model weights are not guaranteed to be present in the public source checkout.
- ZMQ channels have no built-in authentication or encryption.
