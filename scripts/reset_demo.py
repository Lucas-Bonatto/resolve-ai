"""Reset a running local ResolveAI demo without third-party dependencies."""

from __future__ import annotations

import json
from urllib.request import Request, urlopen


def main() -> None:
    request = Request("http://127.0.0.1:8000/api/demo/reset", method="POST")
    with urlopen(request, timeout=10) as response:
        payload = json.load(response)
    print(f"Demo reset: {payload['status']} ({payload['execution']})")


if __name__ == "__main__":
    main()
