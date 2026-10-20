#!/usr/bin/env python3
"""Shared-inbox triage: classify incoming email into routes, flag what's
urgent, and produce a morning triage digest.

Two classifier layers:
  1. rules (default)  — keyword scoring, offline, deterministic, testable
  2. Claude (optional) — set ANTHROPIC_API_KEY and unclear emails (low rule
     confidence) are escalated to the model; the rules stay as fallback

That order is deliberate: the LLM handles the ambiguous 20%, not the boring 80%.

    python3 gen_data.py && python3 triage.py
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import urllib.request

HERE = pathlib.Path(__file__).parent

ROUTES = {
    "booking": {
        "keywords": ["book", "appointment", "schedule", "reschedule", "cancel",
                     "available", "slot", "next week", "come out"],
        "assign": "scheduling team",
    },
    "billing": {
        "keywords": ["invoice", "bill", "charge", "payment", "paid", "refund",
                     "receipt", "card", "overcharg"],
        "assign": "billing",
    },
    "complaint": {
        "keywords": ["unhappy", "disappointed", "terrible", "worst", "complaint",
                     "unacceptable", "still not", "again", "third time", "manager"],
        "assign": "owner",
    },
    "sales": {
        "keywords": ["quote", "estimate", "pricing", "how much", "cost",
                     "interested in", "new customer", "sign up"],
        "assign": "sales",
    },
    "spam": {
        "keywords": ["seo services", "guest post", "backlink", "crypto",
                     "winner", "limited offer", "buy followers"],
        "assign": "trash",
    },
}
URGENT_MARKERS = ["urgent", "asap", "emergency", "immediately", "leak", "flooding",
                  "today please", "right away"]
CONFIDENCE_FLOOR = 2  # rule hits below this -> "other" (or LLM if configured)


def classify_rules(email: dict) -> tuple[str, int]:
    """(route, hit_count). Complaint outranks on ties — angriest first."""
    text = f"{email['subject']} {email['body']}".lower()
    scores = {route: sum(1 for kw in cfg["keywords"] if kw in text)
              for route, cfg in ROUTES.items()}
    priority = ["complaint", "billing", "booking", "sales", "spam"]
    best = max(scores, key=lambda r: (scores[r], -priority.index(r)))
    return (best, scores[best]) if scores[best] >= CONFIDENCE_FLOOR else ("other", scores[best])


def is_urgent(email: dict) -> bool:
    text = f"{email['subject']} {email['body']}".lower()
    return any(m in text for m in URGENT_MARKERS)


def classify_llm(email: dict, api_key: str) -> str | None:
    """Ask Claude to route one ambiguous email. Returns route or None on any failure."""
    body = json.dumps({
        "model": "claude-sonnet-5",
        "max_tokens": 10,
        "messages": [{"role": "user", "content":
                      "Route this customer email for a home-services company. "
                      f"Reply with exactly one word from: {', '.join(ROUTES)} or other.\n\n"
                      f"Subject: {email['subject']}\n\n{email['body'][:1500]}"}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            answer = json.load(resp)["content"][0]["text"].strip().lower()
        return answer if answer in (*ROUTES, "other") else None
    except Exception:
        return None  # LLM is an enhancement, never a dependency


def triage(emails: list[dict], api_key: str | None = None) -> list[dict]:
    out = []
    for e in emails:
        route, hits = classify_rules(e)
        via = "rules"
        if route == "other" and api_key:
            llm_route = classify_llm(e, api_key)
            if llm_route:
                route, via = llm_route, "llm"
        out.append({**e, "route": route, "assign": ROUTES.get(route, {}).get("assign", "inbox"),
                    "urgent": is_urgent(e), "via": via})
    return out


def digest(results: list[dict]) -> str:
    lines = ["# Inbox triage digest", ""]
    urgent = [r for r in results if r["urgent"] and r["route"] != "spam"]
    if urgent:
        lines.append("## 🔴 Urgent — handle first")
        lines += [f"- **{r['from']}** → {r['assign']}: {r['subject']}" for r in urgent]
        lines.append("")
    for route in (*ROUTES, "other"):
        group = [r for r in results if r["route"] == route and not r["urgent"]]
        if group:
            lines.append(f"## {route} ({len(group)}) → {group[0]['assign']}")
            lines += [f"- {r['from']}: {r['subject']}" for r in group]
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    emails = json.loads((HERE / "sample_emails.json").read_text())
    results = triage(emails, os.environ.get("ANTHROPIC_API_KEY"))
    (HERE / "triage_digest.md").write_text(digest(results) + "\n")
    counts: dict[str, int] = {}
    for r in results:
        counts[r["route"]] = counts.get(r["route"], 0) + 1
    urgent_n = sum(1 for r in results if r["urgent"] and r["route"] != "spam")
    llm_n = sum(1 for r in results if r["via"] == "llm")
    print(f"{len(results)} emails triaged: " +
          ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) +
          f" | {urgent_n} urgent" +
          (f" | {llm_n} via Claude" if llm_n else " | rules only (no API key set)"))
    print("-> triage_digest.md")


if __name__ == "__main__":
    main()
