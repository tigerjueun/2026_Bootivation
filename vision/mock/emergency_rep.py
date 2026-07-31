from __future__ import annotations

import argparse
import json

import zmq


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="tcp://*:5556")
    parser.add_argument(
        "--snapshot-available",
        action="store_true",
        help="Return snapshot_available=true for every valid request",
    )
    args = parser.parse_args()

    context = zmq.Context.instance()
    socket = context.socket(zmq.REP)
    socket.setsockopt(zmq.LINGER, 0)
    socket.bind(args.bind)

    print(f"[emergency-mock] REP {args.bind}")

    try:
        while True:
            request = socket.recv_json()
            print(
                "[emergency-mock] RX "
                + json.dumps(request, ensure_ascii=False)
            )

            if not isinstance(request, dict):
                socket.send_json({
                    "ok": False,
                    "error": "request must be a JSON object",
                })
                continue

            if request.get("Emergency") is not True:
                socket.send_json({
                    "ok": False,
                    "error": "Emergency must be true",
                })
                continue

            try:
                customer_id = int(request["customer_id"])
            except (KeyError, TypeError, ValueError):
                socket.send_json({
                    "ok": False,
                    "error": "customer_id is required",
                })
                continue

            response = {
                "ok": True,
                "customer_id": customer_id,
                "snapshot_available": bool(
                    args.snapshot_available
                ),
            }
            socket.send_json(response)
            print(
                "[emergency-mock] TX "
                + json.dumps(response, ensure_ascii=False)
            )

    except KeyboardInterrupt:
        pass
    finally:
        socket.close(0)
        context.term()


if __name__ == "__main__":
    main()
