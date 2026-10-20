#!/usr/bin/env python3
"""Deterministic sample inbox: bookings, billing, complaints, sales, spam,
one urgent emergency, and a couple of genuinely ambiguous ones."""
import json
import pathlib

HERE = pathlib.Path(__file__).parent

EMAILS = [
    {"from": "customer01@example.com", "subject": "Can we reschedule Thursday?",
     "body": "Hi, something came up — can we move my Thursday appointment to next week? Any slot Friday works."},
    {"from": "customer02@example.com", "subject": "Question about my invoice",
     "body": "I was charged $149 but my plan says $89/month. Can you check the last payment and send a corrected receipt?"},
    {"from": "customer03@example.com", "subject": "Third time asking",
     "body": "This is the third time the gate was left open after service. Honestly unacceptable. I'd like to speak to a manager."},
    {"from": "customer04@example.com", "subject": "Quote for a 2nd property",
     "body": "You service our home already — how much would it cost to add my rental? Interested in the same weekly plan."},
    {"from": "marketing05@example.com", "subject": "Rank #1 with our SEO services",
     "body": "We offer guest post backlink packages, limited offer, buy followers today!"},
    {"from": "customer06@example.com", "subject": "URGENT - equipment leak",
     "body": "The pump is leaking everywhere, water flooding the equipment pad. Need someone out here immediately!"},
    {"from": "customer07@example.com", "subject": "Available next week?",
     "body": "Want to book a filter service. What slots do you have Tuesday or Wednesday?"},
    {"from": "customer08@example.com", "subject": "Refund status",
     "body": "You said the refund for the canceled visit was processed — my card still shows the charge. Please confirm payment reversal."},
    {"from": "customer09@example.com", "subject": "hey",
     "body": "quick one — is the green stuff on the steps normal after rain? not sure who to ask"},
    {"from": "customer10@example.com", "subject": "Loved the service",
     "body": "Just wanted to say the new tech did a great job this week. Pass it along!"},
]

(HERE / "sample_emails.json").write_text(json.dumps(EMAILS, indent=2) + "\n")
print(f"wrote sample_emails.json: {len(EMAILS)} emails")
