"""Run the trajectory evals and write structured metrics.

    python -m evals.run_evals                      # offline: scripted model + mocked Open-Meteo (fast, no credentials)
    python -m evals.run_evals --live               # real Azure AI Foundry Claude deployment + real Open-Meteo
    python -m evals.run_evals --live --judge       # ... plus LLM-as-judge itinerary quality scores
    python -m evals.run_evals --cases happy_path,prompt_injection

Results are printed and saved to evals/results/<timestamp>-<mode>.json. The exit code is non-zero if any case fails.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.graph import Deps, build_graph
from agent.settings import ConfigError, get_settings
from evals.harness import CaseResult, load_cases, run_case, tool_names

RESULTS_DIR = Path(__file__).with_name("results")


def offline_graph(case: dict[str, Any]):
    """Graph with a scripted stand-in model and a mocked Open-Meteo transport (see tests/fakes.py)."""
    import httpx

    from tests.fakes import TODAY, ScriptedLLM, weather_transport

    rainy = set(case.get("offline_weather", {}).get("rainy_day_offsets", []))
    deps = Deps(llm=ScriptedLLM(), settings=get_settings(), http_client=httpx.Client(transport=weather_transport(rainy or None)), today=lambda: TODAY)
    return build_graph(deps)


def live_graph():
    """Graph wired to the production LLM client (Azure AI Foundry) and the real Open-Meteo API."""
    from agent.llm_client import get_llm

    return build_graph(Deps(llm=get_llm(), settings=get_settings()))


def summarise_case(result: CaseResult, judge_scores: list[dict[str, Any] | None], seconds: float) -> dict[str, Any]:
    turns = []
    for turn, judged in zip(result.turns, judge_scores):
        st = turn.state
        report = st.get("budget_report") or {}
        turns.append({
            "user": turn.user,
            "tool_sequence": tool_names(st),
            "steps": st.get("step_count"),
            "version": st.get("version"),
            "error": st.get("error"),
            "total_cost": (st.get("itinerary") or {}).get("total_cost"),
            "budget_status": report.get("status"),
            "failures": turn.failures,
            "judge": judged,
        })
    return {"id": result.case_id, "passed": result.passed, "seconds": round(seconds, 2), "turns": turns}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="use the real Azure AI Foundry deployment and Open-Meteo")
    parser.add_argument("--judge", action="store_true", help="score itinerary quality with the LLM judge (requires --live)")
    parser.add_argument("--cases", default="", help="comma-separated case ids (default: all)")
    parser.add_argument("--out", default="", help="results file (default: evals/results/<timestamp>-<mode>.json)")
    args = parser.parse_args(argv)

    if args.judge and not args.live:
        parser.error("--judge runs on the production Azure AI Foundry deployment, so it needs --live (there is no fallback provider)")

    cases = load_cases()
    if args.cases:
        wanted = {c.strip() for c in args.cases.split(",") if c.strip()}
        unknown = wanted - {c["id"] for c in cases}
        if unknown:
            parser.error(f"unknown case ids: {', '.join(sorted(unknown))}")
        cases = [c for c in cases if c["id"] in wanted]

    settings = get_settings()
    judge_llm = None
    if args.live:
        try:
            from agent.llm_client import get_llm

            judge_llm = get_llm()
        except ConfigError as exc:
            print(f"Cannot run live evals: {exc}", file=sys.stderr)
            return 2
    mode = "live" if args.live else "offline"

    summaries: list[dict[str, Any]] = []
    for case in cases:
        graph = live_graph() if args.live else offline_graph(case)
        started = time.perf_counter()
        try:
            result = run_case(case, graph, settings, live=args.live)
        except Exception as exc:  # noqa: BLE001 - report the case as failed rather than aborting the whole run
            print(f"  FAIL {case['id']}: {type(exc).__name__}: {exc}")
            summaries.append({"id": case["id"], "passed": False, "seconds": round(time.perf_counter() - started, 2),
                              "turns": [], "crash": f"{type(exc).__name__}: {exc}"})
            continue
        judged: list[dict[str, Any] | None] = []
        for turn in result.turns:
            scores = None
            if args.judge and turn.state.get("itinerary"):
                from evals.judge import judge_itinerary

                s = judge_itinerary(judge_llm, turn.user, turn.state)
                scores = {**s.model_dump(), "mean": round(s.mean, 2)}
            judged.append(scores)
        summary = summarise_case(result, judged, time.perf_counter() - started)
        summaries.append(summary)
        print(f"  {'PASS' if result.passed else 'FAIL'} {case['id']} ({summary['seconds']}s)")
        for failure in result.failures:
            print(f"       - {failure}")

    passed = sum(1 for s in summaries if s["passed"])
    judged_means = [t["judge"]["mean"] for s in summaries for t in s["turns"] if t.get("judge")]
    report = {
        "mode": mode,
        "model": "scripted stand-in (offline)" if not args.live else f"Azure AI Foundry deployment '{settings.azure_ai_foundry_deployment_name}'",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cases": summaries,
        "aggregate": {
            "cases": len(summaries), "passed": passed, "pass_rate": round(passed / max(1, len(summaries)), 3),
            "judge_mean": round(sum(judged_means) / len(judged_means), 2) if judged_means else None,
            "judged_itineraries": len(judged_means),
        },
    }
    out = Path(args.out) if args.out else RESULTS_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{mode}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    agg = report["aggregate"]
    print(f"\n{mode}: {agg['passed']}/{agg['cases']} cases passed" + (f", judge mean {agg['judge_mean']}/5" if agg["judge_mean"] else "") + f"  ->  {out}")
    return 0 if passed == len(summaries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
