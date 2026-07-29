# Evidence capture request

미결제·도난 시 Fusion PUSH → Vision PULL `tcp://VISION_PC_IP:5557` 권장.

```json
{"command":"CAPTURE_EVIDENCE","customer_id":100,"reason":"UNPAID_EXIT","picked":{"A":2,"B":1,"C":1},"paid":{"A":0,"B":0,"C":0},"unpaid":{"A":2,"B":1,"C":1}}
```

Vision은 이미지·추적 결과·시각을 저장하고 추후 ACK 계약을 추가합니다.
