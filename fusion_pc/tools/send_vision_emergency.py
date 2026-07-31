from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from bootivation_fusion.adapters.vision_emergency import VisionEmergencyClient


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a Bootivation Emergency request to Vision WebUI."
    )
    parser.add_argument(
        "customer_id",
        type=int,
        help="Global Vision customer ID",
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="Example: tcp://192.168.0.20:5556",
    )
    parser.add_argument("--timeout-ms", type=int, default=3000)
    parser.add_argument("--retries", type=int, default=1)
    args = parser.parse_args()

    client = VisionEmergencyClient(
        args.endpoint,
        timeout_ms=args.timeout_ms,
        retries=args.retries,
    )

    try:
        response = client.send(args.customer_id)
    except Exception as error:
        raise SystemExit(str(error)) from error

    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
