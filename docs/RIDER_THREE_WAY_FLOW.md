# Rider 3-way verification

## Correct contract

1. `order_items`: order received from app/server.
2. `rider_removed`: physical shelf removals detected by Vision.
3. `rider_checked_items`: items checked at the ATmega128 Rider POS before leaving.

The final green state is allowed only when all three dictionaries are equal.

## Flow

```text
order A=1,B=1,C=1
→ BLUE + SERVO:A
→ Vision REMOVE_CANDIDATE:A
→ SERVO:B
→ Vision REMOVE_CANDIDATE:B
→ SERVO:C
→ Vision REMOVE_CANDIDATE:C
→ BLUE + SERVO:HOME + RIDER_COLLECTED_WAIT_POS
→ Rider approaches POS and selects RIDER
→ POS checks A/B/C
→ DONE
→ order == vision removed == POS checked
→ GREEN + HOME + PICKUP_COMPLETE
```

A POS Rider scan is verification only. It must not be counted as a physical shelf removal and must not decrement inventory a second time.

`inventory_removed_items` is updated only from Vision removal events.
