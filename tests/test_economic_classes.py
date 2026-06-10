import unittest

from api.economic_classes import (
    build_economic_breakdown,
    build_provider_usage_breakdown,
    classify_provider_economic_class,
    get_provider_catalog,
)


class EconomicClassTests(unittest.TestCase):
    def test_classifies_known_hermes_billing_providers(self):
        cases = {
            "openrouter": "usage_billable",
            "openai-api": "usage_billable",
            "anthropic": "usage_billable",
            "deepseek": "usage_billable",
            "openai-codex": "subscription_based",
            "github-copilot": "subscription_based",
            "kimi-coding-plan": "subscription_based",
            "lm-studio": "oss",
            "ollama": "oss",
            "local": "oss",
            "custom": "oss",
            "custom-direct-api": "oss",
            "unknown-provider": "unknown",
        }

        for provider, expected_class in cases.items():
            with self.subTest(provider=provider):
                self.assertEqual(classify_provider_economic_class(provider), expected_class)

    def test_builds_token_breakdown_from_billing_provider_totals(self):
        provider_rows = [
            {"billing_provider": "openrouter", "total_tokens": 100},
            {"billing_provider": "openai-codex", "total_tokens": 80},
            {"billing_provider": "ollama", "total_tokens": 20},
            {"billing_provider": "unknown-provider", "total_tokens": 7},
        ]

        breakdown = build_economic_breakdown(provider_rows)

        self.assertEqual(breakdown, [
            {"class": "usage_billable", "label": "Usage-billable", "tokens": 100},
            {"class": "oss", "label": "OSS", "tokens": 20},
            {"class": "subscription_based", "label": "Subscription-based", "tokens": 80},
            {"class": "unknown", "label": "Unknown", "tokens": 7},
        ])

    def test_exposes_full_hermes_provider_catalog(self):
        catalog = {provider["key"]: provider["economicClass"] for provider in get_provider_catalog()}

        self.assertGreaterEqual(len(catalog), 42)
        self.assertEqual(catalog["openrouter"], "usage_billable")
        self.assertEqual(catalog["openai-codex"], "subscription_based")
        self.assertEqual(catalog["github-copilot"], "subscription_based")
        self.assertEqual(catalog["lm-studio"], "oss")
        self.assertEqual(catalog["custom"], "oss")
        self.assertEqual(catalog["custom-direct-api"], "oss")
        self.assertEqual(catalog["ollama-gpt-oss"], "oss")

    def test_builds_provider_usage_breakdown_without_hiding_available_catalog(self):
        provider_rows = [
            {"billing_provider": "openrouter", "total_tokens": 100, "session_count": 2, "models": "a,b"},
            {"billing_provider": "openai-codex", "total_tokens": 80, "session_count": 1, "models": "gpt-5.4"},
            {"billing_provider": "custom", "total_tokens": 20, "session_count": 1, "models": "gpt-oss:20b"},
        ]

        breakdown = build_provider_usage_breakdown(provider_rows)

        self.assertEqual(breakdown, [
            {
                "provider": "openrouter",
                "label": "OpenRouter",
                "economicClass": "usage_billable",
                "economicLabel": "Usage-billable",
                "tokens": 100,
                "sessions": 2,
                "models": ["a", "b"],
            },
            {
                "provider": "openai-codex",
                "label": "OpenAI Codex",
                "economicClass": "subscription_based",
                "economicLabel": "Subscription-based",
                "tokens": 80,
                "sessions": 1,
                "models": ["gpt-5.4"],
            },
            {
                "provider": "custom",
                "label": "Custom local endpoint",
                "economicClass": "oss",
                "economicLabel": "OSS",
                "tokens": 20,
                "sessions": 1,
                "models": ["gpt-oss:20b"],
            },
        ])

    def test_same_model_can_have_different_economic_classes_by_provider(self):
        provider_rows = [
            {"model": "gpt-5.4", "billing_provider": "openai-codex", "total_tokens": 80},
            {"model": "gpt-5.4", "billing_provider": "openrouter", "total_tokens": 20},
        ]

        breakdown = build_economic_breakdown(provider_rows)

        self.assertEqual(breakdown, [
            {"class": "usage_billable", "label": "Usage-billable", "tokens": 20},
            {"class": "oss", "label": "OSS", "tokens": 0},
            {"class": "subscription_based", "label": "Subscription-based", "tokens": 80},
            {"class": "unknown", "label": "Unknown", "tokens": 0},
        ])


if __name__ == "__main__":
    unittest.main()
