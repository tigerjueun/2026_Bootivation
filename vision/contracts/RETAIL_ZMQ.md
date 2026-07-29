# Retail customer-state ZMQ

Ubuntu ROS2 Vision PUB `tcp://*:5555`, Fusion SUB. Topic prefix `retail`.

```text
retail {"timestamp":1784902629.0,"customer_id":100,"active":true,"visit_state":"inside","zone_A_picks":2,"zone_B_picks":1,"zone_C_picks":1,"at_kiosk":false,"event":null}
```

Fusion은 누적 픽업 수량의 증가분만 REMOVE_CANDIDATE A/B/C로 변환합니다.
