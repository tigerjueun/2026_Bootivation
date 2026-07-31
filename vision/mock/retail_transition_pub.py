from __future__ import annotations

import argparse
import json
import time

import zmq


PRODUCTS = ("A", "B", "C")


def parse_counts(text: str) -> dict[str, int]:
    result = {product: 0 for product in PRODUCTS}

    if not text.strip():
        return result

    for token in text.split(","):
        name, separator, quantity = token.strip().partition("=")
        if separator != "=":
            raise ValueError(f"Invalid count token: {token!r}")

        product = name.upper()
        if product not in result or not quantity.isdigit():
            raise ValueError(f"Invalid count token: {token!r}")

        result[product] = int(quantity)

    return result


def make_payload(
    state: str,
    customer_id: int,
    counts: dict[str, int],
) -> dict:
    is_exit = state == "EXIT"

    return {
        "timestamp": time.time(),
        "customer_id": customer_id,
        "state": state,
        "active": not is_exit,
        "visit_state": "released" if is_exit else "inside",
        "zone_A_picks": counts["A"],
        "zone_B_picks": counts["B"],
        "zone_C_picks": counts["C"],
        "at_kiosk": not is_exit,
        "event": "exit" if is_exit else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="tcp://*:5555")
    parser.add_argument("--topic", default="retail")
    args = parser.parse_args()

    context = zmq.Context.instance()
    socket = context.socket(zmq.PUB)
    socket.setsockopt(zmq.LINGER, 0)
    socket.bind(args.bind)

    print(f"[vision-mock] PUB {args.bind} topic={args.topic!r}")
    print("Start Fusion first, wait about one second, then use:")
    print("  pos 100 A=2,B=1,C=1")
    print("  exit 100 A=2,B=1,C=1")
    print("  q")
    time.sleep(1.0)

    try:
        while True:
            line = input("vision> ").strip()
            if not line:
                continue
            if line.lower() == "q":
                break

            parts = line.split(maxsplit=2)
            if len(parts) < 2:
                print("Usage: pos|exit <customer_id> [A=1,B=1,C=1]")
                continue

            state = parts[0].upper()
            if state not in {"POS", "EXIT"}:
                print("First token must be pos or exit")
                continue

            if not parts[1].isdigit():
                print("customer_id must be an integer")
                continue

            try:
                product_counts = parse_counts(
                    parts[2] if len(parts) == 3 else ""
                )
            except ValueError as error:
                print(error)
                continue

            payload = make_payload(
                state,
                int(parts[1]),
                product_counts,
            )
            message = args.topic + " " + json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            socket.send_string(message)
            print("[vision-mock] TX", message)

    except KeyboardInterrupt:
        pass
    finally:
        socket.close(0)


if __name__ == "__main__":
    main()
