"""python3 -m unittest — rules layer only; no network."""
import unittest

from triage import classify_rules, digest, is_urgent, triage


def email(subject, body, sender="x@example.com"):
    return {"from": sender, "subject": subject, "body": body}


class RulesTest(unittest.TestCase):
    def test_booking(self):
        route, _ = classify_rules(email("Reschedule?", "can we schedule another appointment slot"))
        self.assertEqual(route, "booking")

    def test_billing(self):
        route, _ = classify_rules(email("Invoice issue", "the charge on my payment receipt looks wrong"))
        self.assertEqual(route, "billing")

    def test_complaint_outranks_on_overlap(self):
        # mentions invoice AND is angry -> owner sees it, not billing
        route, _ = classify_rules(email(
            "Unacceptable", "third time this invoice is wrong, I'm disappointed, manager please — unacceptable"))
        self.assertEqual(route, "complaint")

    def test_spam(self):
        route, _ = classify_rules(email("SEO services", "guest post backlink limited offer"))
        self.assertEqual(route, "spam")

    def test_ambiguous_goes_to_other_not_a_guess(self):
        route, hits = classify_rules(email("hey", "is the green stuff on the steps normal?"))
        self.assertEqual(route, "other")

    def test_urgency(self):
        self.assertTrue(is_urgent(email("URGENT leak", "water flooding everywhere")))
        self.assertFalse(is_urgent(email("hi", "all good this week")))


class TriageTest(unittest.TestCase):
    def test_no_api_key_stays_offline(self):
        results = triage([email("hey", "unclear question")], api_key=None)
        self.assertEqual(results[0]["route"], "other")
        self.assertEqual(results[0]["via"], "rules")

    def test_digest_puts_urgent_first(self):
        results = triage([
            email("URGENT leak", "flooding at the pad", "customer06@example.com"),
            email("book me", "schedule an appointment slot please"),
        ], api_key=None)
        text = digest(results)
        self.assertLess(text.index("Urgent"), text.index("booking"))

    def test_urgent_spam_not_in_urgent_section(self):
        results = triage([email("URGENT limited offer", "buy followers backlink guest post asap")],
                         api_key=None)
        self.assertNotIn("🔴", digest(results))


if __name__ == "__main__":
    unittest.main()
