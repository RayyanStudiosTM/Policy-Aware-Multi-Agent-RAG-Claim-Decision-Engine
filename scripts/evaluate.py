#!/usr/bin/env python3
"""
Evaluate the Aptino Policy-Aware Claim Decision Engine.

Usage:
    python scripts/evaluate.py

Optional:
    python scripts/evaluate.py --base-url http://127.0.0.1:8000
    python scripts/evaluate.py --public data/public_cases/public_test_cases.json
    python scripts/evaluate.py --custom data/custom_cases/custom_test_cases.json
    python scripts/evaluate.py --timeout 180

The script sends each case to POST /analyze and stores the raw responses.
It does not invent expected decisions. Expected values should be added to
the input datasets or evaluated separately against the supplied assignment
ground truth.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC = ROOT / "data" / "public_cases" / "public_test_cases.json"
DEFAULT_CUSTOM = ROOT / "data" / "custom_cases" / "custom_test_cases.json"
OUTPUT_DIR = ROOT / "evaluation"


def load_cases(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Case file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # Support common wrappers used by test datasets.
        for key in ("cases", "test_cases", "public_cases", "custom_cases"):
            if isinstance(data.get(key), list):
                return data[key]

    raise ValueError(
        f"{path} must contain a JSON list or an object containing a case list."
    )


def analyze_case(base_url: str, case: dict, timeout: int):
    url = base_url.rstrip("/") + "/analyze"
    payload = json.dumps({"case": case}).encode("utf-8")

    request = Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()

    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            body = json.loads(raw)

            return {
                "case_id": case.get("case_id", "UNKNOWN"),
                "status": "OK",
                "http_status": response.status,
                "duration_ms": elapsed_ms,
                "response": body,
            }

    except HTTPError as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = str(exc)

        return {
            "case_id": case.get("case_id", "UNKNOWN"),
            "status": "HTTP_ERROR",
            "http_status": exc.code,
            "duration_ms": elapsed_ms,
            "error": detail,
        }

    except (URLError, TimeoutError, OSError) as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

        return {
            "case_id": case.get("case_id", "UNKNOWN"),
            "status": "CONNECTION_ERROR",
            "http_status": None,
            "duration_ms": elapsed_ms,
            "error": str(exc),
        }

    except json.JSONDecodeError as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

        return {
            "case_id": case.get("case_id", "UNKNOWN"),
            "status": "INVALID_JSON",
            "http_status": None,
            "duration_ms": elapsed_ms,
            "error": str(exc),
        }


def summarize(results):
    decisions = {}
    validation = {}
    needs_review = []
    successful = 0
    failed = 0
    durations = []

    for item in results:
        if item["status"] != "OK":
            failed += 1
            continue

        successful += 1
        durations.append(item["duration_ms"])

        response = item.get("response", {})
        decision = response.get("decision", "UNKNOWN")
        decisions[decision] = decisions.get(decision, 0) + 1

        validation_status = (
            response.get("validation", {}) or {}
        ).get("status", "UNKNOWN")
        validation[validation_status] = validation.get(validation_status, 0) + 1

        if decision == "NEEDS_REVIEW":
            needs_review.append(item["case_id"])

    return {
        "total": len(results),
        "successful": successful,
        "failed": failed,
        "decisions": decisions,
        "validation": validation,
        "needs_review_cases": needs_review,
        "average_duration_ms": (
            round(sum(durations) / len(durations), 2) if durations else None
        ),
    }


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def run_group(name, path, base_url, timeout):
    print(f"\n{'=' * 70}")
    print(f"{name.upper()} CASES")
    print(f"Input: {path}")
    print(f"{'=' * 70}")

    cases = load_cases(path)
    print(f"Loaded {len(cases)} cases.")

    results = []

    for index, case in enumerate(cases, start=1):
        case_id = case.get("case_id", f"CASE-{index}")
        print(f"[{index}/{len(cases)}] {case_id} ...", end=" ", flush=True)

        result = analyze_case(base_url, case, timeout)
        results.append(result)

        if result["status"] == "OK":
            response = result["response"]
            decision = response.get("decision", "UNKNOWN")
            validation = (response.get("validation") or {}).get(
                "status", "UNKNOWN"
            )
            print(
                f"OK | {decision} | validation={validation} | "
                f"{result['duration_ms']} ms"
            )
        else:
            print(f"{result['status']} | {result.get('error', '')}")

    summary = summarize(results)

    print("\nSummary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    return cases, results, summary


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate the Aptino claim decision engine."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="FastAPI base URL (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--public",
        type=Path,
        default=DEFAULT_PUBLIC,
        help="Public cases JSON file",
    )
    parser.add_argument(
        "--custom",
        type=Path,
        default=DEFAULT_CUSTOM,
        help="Custom cases JSON file",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Per-case HTTP timeout in seconds",
    )

    args = parser.parse_args()

    # Normalize relative paths against project root.
    public_path = args.public if args.public.is_absolute() else ROOT / args.public
    custom_path = args.custom if args.custom.is_absolute() else ROOT / args.custom

    # Check backend before sending the full evaluation.
    health_url = args.base_url.rstrip("/") + "/health"
    print(f"Checking backend: {health_url}")

    try:
        with urlopen(health_url, timeout=15) as response:
            health = json.loads(response.read().decode("utf-8"))
            print(f"Backend health: {health}")
    except Exception as exc:
        print(
            "\nERROR: Backend health check failed.\n"
            "Start FastAPI first, for example:\n\n"
            "  uvicorn backend.api.main:app\n\n"
            f"Details: {exc}\n",
            file=sys.stderr,
        )
        return 1

    try:
        public_cases, public_results, public_summary = run_group(
            "public", public_path, args.base_url, args.timeout
        )
        custom_cases, custom_results, custom_summary = run_group(
            "custom", custom_path, args.base_url, args.timeout
        )
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    timestamp = datetime.now(timezone.utc).isoformat()

    public_output = {
        "generated_at_utc": timestamp,
        "base_url": args.base_url,
        "source_file": str(public_path),
        "cases": public_results,
        "summary": public_summary,
    }

    custom_output = {
        "generated_at_utc": timestamp,
        "base_url": args.base_url,
        "source_file": str(custom_path),
        "cases": custom_results,
        "summary": custom_summary,
    }

    combined = {
        "generated_at_utc": timestamp,
        "base_url": args.base_url,
        "public": public_summary,
        "custom": custom_summary,
        "total_cases": len(public_results) + len(custom_results),
        "total_successful": (
            public_summary["successful"] + custom_summary["successful"]
        ),
        "total_failed": public_summary["failed"] + custom_summary["failed"],
        "total_needs_review": (
            len(public_summary["needs_review_cases"])
            + len(custom_summary["needs_review_cases"])
        ),
    }

    save_json(OUTPUT_DIR / "public_results.json", public_output)
    save_json(OUTPUT_DIR / "custom_results.json", custom_output)
    save_json(OUTPUT_DIR / "evaluation_summary.json", combined)

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print(json.dumps(combined, indent=2, ensure_ascii=False))
    print("\nSaved:")
    print(f"  {OUTPUT_DIR / 'public_results.json'}")
    print(f"  {OUTPUT_DIR / 'custom_results.json'}")
    print(f"  {OUTPUT_DIR / 'evaluation_summary.json'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
