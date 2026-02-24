#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def get_env_int(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    try:
        parsed = int(value)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got: {value!r}") from None

    if parsed < 1:
        raise ValueError(f"{name} must be >= 1, got: {parsed}")

    return parsed


def post_json_line(webhook_url: str, line: str, timeout: int) -> str:
    result = subprocess.run(
        [
            "curl",
            "-sS",
            "-X",
            "POST",
            webhook_url,
            "-H",
            "Content-Type: application/json",
            "--data",
            line,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode == 0:
        return result.stdout
    stderr = result.stderr.strip()
    return f"curl failed (exit {result.returncode}): {stderr}"


def main() -> int:
    log_file = Path(os.getenv("LOG_FILE", "./webhook_events_direct.log"))
    webhook_url = os.getenv("WEBHOOK_URL", "http://localhost:8000/webhook")
    try:
        concurrency = get_env_int("CONCURRENCY", 10)
        timeout = get_env_int("REQUEST_TIMEOUT", 10)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not log_file.is_file():
        print(f"Log file not found: {log_file}", file=sys.stderr)
        return 1

    if shutil.which("curl") is None:
        print("curl is required but was not found in PATH", file=sys.stderr)
        return 1

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        with log_file.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line:
                    continue
                futures.append(executor.submit(post_json_line, webhook_url, line, timeout))

        for future in as_completed(futures):
            print(future.result())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
