"""P-06 eval runner: triage agent over 30 replies, binary checks, results file.

Checks per case: status match, need match, quote grounded (substring of
reply), LLM-judge (follow-up in resident language, under 320 chars).
Writes evals/results/<date>.md. No prompt changes happen here.
"""

from __future__ import annotations

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NAMES = {"en": "Ruth Alvarez", "es": "Elena Vasquez"}


def judge_followup(reply: str, lang: str, triage) -> bool:
    from strands import Agent
    from strands.models import BedrockModel

    from agent.models import Triage

    followup = "" if triage.status == "ok" else triage.reason
    if not followup:
        return True
    agent = Agent(
        model=BedrockModel(model_id=os.environ.get("BEDROCK_MODEL_ID", ""),
                           region_name=os.environ.get("AWS_REGION", "") or None),
        structured_output_model=Triage,
        system_prompt=("Answer only whether the given follow-up text is written in the "
                       "resident's language and is under 320 characters. Reply with a "
                       "Triage structure; set status ok when it passes, unclear when not."),
    )
    out = agent(f"Resident language {lang}. Reply was: {reply!r}. "
                f"Follow-up text: {followup!r}").structured_output
    return out.status == "ok"


def main() -> int:
    from dotenv import load_dotenv

    load_dotenv()
    from agent.triage import triage_reply

    with open("evals/replies/cases.json", encoding="utf-8") as fh:
        cases = json.load(fh)["cases"]
    rows = []
    for case in cases:
        resident = {"name": NAMES[case["lang"]], "language": case["lang"], "notes": ""}
        try:
            triage, _ = triage_reply(case["reply"], resident)
        except Exception as exc:  # noqa: BLE001 - record, don't stop the run
            rows.append({**case, "got_status": f"ERROR:{type(exc).__name__}",
                         "got_need": "", "quote": "", "checks": {}})
            continue
        quote_ok = bool(triage.quote) and triage.quote in case["reply"]
        try:
            judge_ok = judge_followup(case["reply"], case["lang"], triage)
        except Exception:  # noqa: BLE001 - judge failure counts as fail
            judge_ok = False
        rows.append({
            **case,
            "got_status": triage.status, "got_need": triage.need, "quote": triage.quote,
            "checks": {
                "status": triage.status == case["expected_status"],
                "need": triage.need == case["expected_need"],
                "quote": quote_ok, "judge": judge_ok,
            },
        })
    sm = sum(r["checks"].get("status", False) for r in rows)
    nm = sum(r["checks"].get("need", False) for r in rows)
    qg = sum(r["checks"].get("quote", False) for r in rows)
    jp = sum(r["checks"].get("judge", False) for r in rows)
    date = datetime.date.today().isoformat()
    lines = [f"# Eval results {date}", "",
             f"status_match={sm}/30 need_match={nm}/30 quote_grounded={qg}/30 judge_pass={jp}/30", "",
             "| id | reply | expected | got | S | N | Q | J | failure_mode |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        c = r["checks"]
        flag = lambda b: "Y" if b else "N"  # noqa: E731
        rep = r["reply"][:44].replace("|", "/")
        lines.append(f"| {r['id']} | {rep} | {r['expected_status']}/{r['expected_need']} | "
                     f"{r.get('got_status')}/{r.get('got_need')} | {flag(c.get('status'))} | "
                     f"{flag(c.get('need'))} | {flag(c.get('quote'))} | {flag(c.get('judge'))} |  |")
    lines += ["", "## Failure-mode labels (owner fills after first run)", "",
              "Modes: missed-medical-cue, false-medical-figurative, wrong-language, "
              "caregiver-confusion, opt-out-not-honored, need-mismatch, quote-ungrounded, judge-fail."]
    os.makedirs("evals/results", exist_ok=True)
    with open(f"evals/results/{date}.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"PROOF P-06: 30 replies status_match={sm} need_match={nm} quote_grounded={qg} "
          f"judge_pass={jp}")
    print(f"results written to evals/results/{date}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
