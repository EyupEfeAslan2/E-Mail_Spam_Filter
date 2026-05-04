import os
import tempfile
import unittest

import pandas as pd

from core.adaptive import AdaptiveSystem
from core.bloom_filter import BloomFilter
from core.rate_limit import SlidingWindowRateLimiter
from core.retrain import RetrainQueue
from core.security import privacy_hash, redact_email_text


class DummyFilter:
    def __init__(self):
        self.spam = []
        self.ham = []

    def add_spam_signature(self, cleaned_text):
        self.spam.append(cleaned_text)

    def allow_ham_signature(self, cleaned_text):
        self.ham.append(cleaned_text)


class CoreBehaviourTests(unittest.TestCase):
    def test_bloom_filter_persists_membership(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bloom.bin")
            first = BloomFilter(size=1024, hash_count=3, storage_path=path)
            first.add("limited time offer")
            first.save()

            second = BloomFilter(size=1024, hash_count=3, storage_path=path)
            self.assertTrue(second.check("limited time offer"))
            self.assertFalse(second.check("quarterly invoice"))

    def test_privacy_hash_is_stable_and_redaction_masks_pii(self):
        self.assertEqual(privacy_hash("abc", salt="s"), privacy_hash("abc", salt="s"))
        redacted = redact_email_text("mail me at alice@example.com or +90 555 111 2233")
        self.assertNotIn("alice@example.com", redacted)
        self.assertNotIn("555 111 2233", redacted)

    def test_adaptive_feedback_writes_redacted_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports = os.path.join(tmp, "reports.csv")
            old_reports = os.environ.get("SPAM_REPORTS_FILE")
            os.environ["SPAM_REPORTS_FILE"] = reports
            try:
                system = AdaptiveSystem(DummyFilter())
                system.reports_file = reports
                pd.DataFrame(
                    columns=[
                        "created_at",
                        "label",
                        "text_redacted",
                        "text_hash",
                        "text_cleaned_hash",
                        "feedback_type",
                    ]
                ).to_csv(reports, index=False)
                system.report_spam("Contact bob@example.com for free prize")
                saved = pd.read_csv(reports)
                self.assertIn("text_hash", saved.columns)
                self.assertNotIn("bob@example.com", saved.iloc[0]["text_redacted"])
            finally:
                if old_reports is None:
                    os.environ.pop("SPAM_REPORTS_FILE", None)
                else:
                    os.environ["SPAM_REPORTS_FILE"] = old_reports

    def test_retrain_queue_persists_request_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "retrain.json")
            queue = RetrainQueue(state_path=path)
            state = queue.enqueue("unit_test")

            self.assertTrue(state["requested"])
            self.assertEqual("unit_test", state["reason"])
            self.assertTrue(RetrainQueue(state_path=path).read()["requested"])

    def test_sliding_window_rate_limiter_blocks_excess_requests(self):
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)

        self.assertTrue(limiter.allow("client"))
        self.assertTrue(limiter.allow("client"))
        self.assertFalse(limiter.allow("client"))


if __name__ == "__main__":
    unittest.main()
