# Event and Action Scenario Matrix

## 1. Customer payment scenarios

At customer EXIT, Fusion compares:

```text
picked  = final Vision EXIT A/B/C counts
paid    = customer-associated POS payment
unpaid  = max(picked - paid, 0)
overpaid = max(paid - picked, 0)
```

| Situation | Calculation | Result code | Automatic action | Operator view |
|---|---|---|---|---|
| exits without items | `sum(picked)=0` | `NO_ITEMS` | no alarm | information event |
| exact payment | `picked=paid` | `CLEARED` | normal completion | success result |
| bypasses POS with items | `paid=0`, `picked>0`, no POS transition | `BYPASS_POS_NO_PAYMENT` | Rider RED + RPi warning + Vision Emergency 5556 | critical alert and customer ID/image |
| reaches POS but pays nothing | `paid=0`, `picked>0`, POS seen | `NO_PAYMENT` | Rider RED + RPi warning + Vision Emergency 5556 | critical alert |
| partial payment | any `unpaid>0`, `sum(paid)>0` | `PARTIAL_PAYMENT` | same critical actions | A/B/C unpaid difference |
| paid quantity exceeds PICK | any `overpaid>0`, `unpaid=0` | `OVERPAYMENT` | no theft alarm | warning and difference |
| entry tracking cancelled with no PICK | `picked=0` | `NO_ITEMS` | ignore alarm path | timeline only |

### Emergency response

```text
Fusion REQ :5556
{"Emergency":true,"customer_id":100}

Vision WebUI REP
{"ok":true,"customer_id":100,"snapshot_available":true}
```

The WebUI displays a red theft warning and the Camera 1 entry snapshot when available.

---

## 2. Rider scenarios

Three independent ledgers are used:

```text
order_items
rider_removed       # Vision physical shelf removal
rider_checked_items # Rider POS final verification
```

| Situation | Calculation | Automatic action | Result |
|---|---|---|---|
| order accepted | set `order_items` | BLUE + first item servo | `RIDER_ORDER_READY` |
| valid item collected | `removed[item] <= order[item]` | guide next missing item | progress update |
| unordered/extra item | `removed[item] > order[item]` or order 0 | RED | `WRONG_PICKUP:<item>` |
| all physical items collected | `order=removed` | BLUE + HOME, ask for Rider POS check | `RIDER_COLLECTED_WAIT_POS` |
| POS checks too few/many | `checked != order` at DONE | RED | `RIDER_POS_MISMATCH` |
| physical removal differs | `removed != order` at DONE | RED | `RIDER_REMOVAL_MISMATCH` |
| final three-way match | `order=removed=checked` | GREEN + HOME | `PICKUP_COMPLETE` |

The POS Rider scan is verification only; it must not decrement inventory a second time.

---

## 3. Checkout tray scenarios

```text
expected = POS CUSTOMER payment
before   = stabilized BEFORE tray count
after    = stabilized AFTER tray count
missing  = max(expected - after, 0)
extra    = max(after - expected, 0)
```

| Situation | Result | Action |
|---|---|---|
| products appear on BEFORE | `SCANNING` | `scan_product.wav` |
| customer POS payment confirmed | `WAIT_TRANSFER` | `scan_completed.wav`, store expected |
| `before=0` and `after=expected` | `TRAY_COMPLETE` | normal completion |
| same total but wrong classes | `TRAY_MISMATCH` | warning WAV and dashboard alert |
| missing item after transfer timeout | `TRAY_MISMATCH` | show A/B/C missing |
| extra item | `TRAY_MISMATCH` | show A/B/C extra |
| system reset | `WAIT_BEFORE` | `system_reset.wav` then place-before guidance |

---

## 4. Device and transport conditions

| Device/channel | What can be monitored | Correct interpretation |
|---|---|---|
| POS serial | COM open, latest line, boot count | repeated unsolicited BOOT may indicate power instability |
| Rider serial | COM open and commanded actuator result | port open alone does not prove servo movement |
| RPi 5562 | periodic `TRAY_COUNT` timestamp | a configurable stale timeout is meaningful |
| Vision 5555 | listener reachability and latest POS/EXIT transition | **do not use a 4-second stale rule**; final upstream is intentionally one-shot |
| Vision 5556 | REQ/REP response and timeout | recreate REQ socket after timeout |
| RPi 5563 | command send result | no application ACK in the current contract |

Because Vision 5555 does not publish a heartbeat, health monitoring should use a separate heartbeat or service check rather than the absence of customer events.

---

## 5. Operator actions

Current archive exposes:

```text
status
rpi
vision
order A=1,B=1,C=1
event REMOVE_CANDIDATE:A
audio TRAY_MISMATCH
rpi-reset
emergency 100
reset
quit
```

The HTTP dashboard exposes current Fusion, Vision, RPi, customer and alert JSON. Authentication and a full production control surface are outside the hackathon scope.

---

## 6. Intentional limits

- Final Fusion demonstration is centered on one active customer/payment correlation at a time.
- Vision 5555 sends POS/EXIT transitions, not a continuous heartbeat or every PICK frame.
- RETURN and quantity decrement are not implemented by the final Vision pipeline.
- RPi HSV classification assumes a fixed camera/tray installation.
- ZMQ channels have no authentication or encryption.
- Emergency snapshot display depends on the Vision WebUI having captured that customer's Camera 1 entry image.
