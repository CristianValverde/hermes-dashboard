import os
import tempfile
import textwrap
import unittest

from api.agent_log_metrics import parse_agent_log_metrics


class AgentLogMetricsTests(unittest.TestCase):
    def test_parses_response_metrics_from_full_log(self):
        content = textwrap.dedent("""
            2026-06-01 10:00:00,000 INFO gateway.run: response ready: platform=telegram chat=1 time=10.0s api_calls=1 response=100 chars
            2026-06-01 10:10:00,000 WARNING gateway.run: sample warning
            2026-06-01 10:20:00,000 INFO gateway.run: response ready: platform=telegram chat=1 time=20.0s api_calls=2 response=200 chars
            2026-06-02 10:00:00,000 INFO gateway.run: Processing audio with duration 5.0
            2026-06-02 10:10:00,000 INFO gateway.run: switching fallback model
            2026-06-02 10:20:00,000 INFO gateway.run: response ready: platform=telegram chat=1 time=40.0s api_calls=4 response=400 chars
        """).strip()

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as file:
            file.write(content)
            path = file.name

        try:
            metrics = parse_agent_log_metrics(path)
        finally:
            os.unlink(path)

        self.assertEqual(metrics["totalResponses"], 3)
        self.assertEqual(metrics["avgTime"], 23.3)
        self.assertEqual(metrics["medianTime"], 20.0)
        self.assertEqual(metrics["p95Time"], 40.0)
        self.assertEqual(metrics["avgApiCalls"], 2.3)
        self.assertEqual(metrics["avgChars"], 233)
        self.assertEqual(metrics["audioCount"], 1)
        self.assertEqual(metrics["fallbackCount"], 1)
        self.assertEqual(metrics["warningCount"], 1)
        self.assertEqual(metrics["trend"], [
            {"date": "2026-06-01", "avgTime": 15.0, "count": 2},
            {"date": "2026-06-02", "avgTime": 40.0, "count": 1},
        ])


if __name__ == "__main__":
    unittest.main()
