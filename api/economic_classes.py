"""Economic classification for Hermes provider usage.

The source taxonomy mirrors the provider list exposed by `hermes model`.
Keep this backend-side so the dashboard does not infer cost classes in React.
"""

import re

ECONOMIC_CLASS_LABELS = {
    "usage_billable": "Usage-billable",
    "oss": "OSS",
    "subscription_based": "Subscription-based",
    "unknown": "Unknown",
}

ECONOMIC_CLASS_ORDER = ("usage_billable", "oss", "subscription_based", "unknown")

HERMES_PROVIDER_CATALOG = (
    {"key": "nous-portal", "label": "Nous Portal", "economicClass": "subscription_based"},
    {"key": "openrouter", "label": "OpenRouter", "economicClass": "usage_billable"},
    {"key": "novitaai", "label": "NovitaAI", "economicClass": "usage_billable"},
    {"key": "lm-studio", "label": "LM Studio", "economicClass": "oss"},
    {"key": "anthropic", "label": "Anthropic", "economicClass": "usage_billable"},
    {"key": "openai-codex", "label": "OpenAI Codex", "economicClass": "subscription_based"},
    {"key": "openai-api", "label": "OpenAI API", "economicClass": "usage_billable"},
    {"key": "qwen-cloud", "label": "Qwen Cloud / DashScope Coding", "economicClass": "usage_billable"},
    {"key": "xai-oauth", "label": "xAI Grok OAuth", "economicClass": "subscription_based"},
    {"key": "xiaomi", "label": "Xiaomi MiMo", "economicClass": "usage_billable"},
    {"key": "tencent-tokenhub", "label": "Tencent TokenHub", "economicClass": "usage_billable"},
    {"key": "nvidia-nim", "label": "NVIDIA NIM", "economicClass": "usage_billable"},
    {"key": "github-copilot", "label": "GitHub Copilot", "economicClass": "subscription_based"},
    {"key": "github-copilot-acp", "label": "GitHub Copilot ACP", "economicClass": "subscription_based"},
    {"key": "huggingface", "label": "Hugging Face Inference Providers", "economicClass": "oss"},
    {"key": "google-ai-studio", "label": "Google AI Studio", "economicClass": "usage_billable"},
    {"key": "google-oauth", "label": "Google Gemini OAuth / Code Assist", "economicClass": "subscription_based"},
    {"key": "deepseek", "label": "DeepSeek", "economicClass": "usage_billable"},
    {"key": "xai", "label": "xAI", "economicClass": "usage_billable"},
    {"key": "z-ai", "label": "Z.AI / GLM", "economicClass": "usage_billable"},
    {"key": "moonshot-api", "label": "Kimi / Moonshot API", "economicClass": "usage_billable"},
    {"key": "kimi-moonshot-china", "label": "Kimi / Moonshot China", "economicClass": "usage_billable"},
    {"key": "kimi-coding-plan", "label": "Kimi Coding Plan", "economicClass": "subscription_based"},
    {"key": "stepfun-step-plan", "label": "StepFun Step Plan", "economicClass": "subscription_based"},
    {"key": "minimax-global", "label": "MiniMax global direct API", "economicClass": "usage_billable"},
    {"key": "minimax-oauth", "label": "MiniMax OAuth browser login", "economicClass": "subscription_based"},
    {"key": "minimax-china", "label": "MiniMax China", "economicClass": "usage_billable"},
    {"key": "ollama-cloud", "label": "Ollama Cloud", "economicClass": "oss"},
    {"key": "arcee", "label": "Arcee AI", "economicClass": "usage_billable"},
    {"key": "gmi", "label": "GMI Cloud", "economicClass": "usage_billable"},
    {"key": "kilo-code", "label": "Kilo Code", "economicClass": "usage_billable"},
    {"key": "opencode-zen", "label": "OpenCode Zen", "economicClass": "usage_billable"},
    {"key": "opencode-go", "label": "OpenCode Go", "economicClass": "subscription_based"},
    {"key": "aws-bedrock", "label": "AWS Bedrock", "economicClass": "usage_billable"},
    {"key": "azure-foundry", "label": "Azure Foundry", "economicClass": "usage_billable"},
    {"key": "qwen-oauth", "label": "Qwen OAuth", "economicClass": "subscription_based"},
    {"key": "alibaba-coding-plan", "label": "Alibaba Cloud Coding Plan", "economicClass": "subscription_based"},
    {"key": "custom", "label": "Custom local endpoint", "economicClass": "oss"},
    {"key": "custom-direct-api", "label": "Custom direct endpoint", "economicClass": "oss"},
    {"key": "mistral-nemo", "label": "Local custom: Mistral Nemo", "economicClass": "oss"},
    {"key": "qwen-coder", "label": "Local custom: Qwen Coder", "economicClass": "oss"},
    {"key": "phi4-mini", "label": "Local custom: Phi-4 Mini", "economicClass": "oss"},
    {"key": "nemotron-omni", "label": "Local custom: Nemotron Omni", "economicClass": "oss"},
    {"key": "ollama-gpt-oss", "label": "Local custom: Ollama GPT-OSS", "economicClass": "oss"},
)

PROVIDER_CATALOG_BY_KEY = {provider["key"]: provider for provider in HERMES_PROVIDER_CATALOG}

USAGE_BILLABLE_PROVIDERS = {
    "openrouter",
    "novitaai",
    "anthropic",
    "openai-api",
    "dashscope",
    "qwen-cloud",
    "xiaomi",
    "tokenhub",
    "tencent-tokenhub",
    "nvidia",
    "nvidia-nim",
    "google",
    "google-ai-studio",
    "deepseek",
    "xai",
    "zai",
    "z-ai",
    "zhipuai",
    "glm",
    "moonshot",
    "moonshot-api",
    "kimi-moonshot-china",
    "minimax",
    "minimax-global",
    "minimax-china",
    "arcee",
    "gmi",
    "kilo",
    "kilo-code",
    "opencode-zen",
    "aws-bedrock",
    "bedrock",
    "azure-foundry",
    "azure",
}

SUBSCRIPTION_PROVIDERS = {
    "nous",
    "nous-portal",
    "openai-codex",
    "github-copilot",
    "github-copilot-acp",
    "xai-oauth",
    "google-oauth",
    "kimi-coding-plan",
    "stepfun-step-plan",
    "minimax-oauth",
    "opencode-go",
    "alibaba-coding-plan",
    "qwen-oauth",
}

OSS_PROVIDERS = {
    "lm-studio",
    "huggingface",
    "hugging-face",
    "ollama",
    "ollama-cloud",
    "local",
    "custom",
    "custom-direct-api",
    "mistral-nemo",
    "qwen-coder",
    "phi4-mini",
    "nemotron-omni",
    "ollama-gpt-oss",
}

PROVIDER_ALIASES = {
    "alibaba-cloud-coding-plan": "alibaba-coding-plan",
    "anthropic-api": "anthropic",
    "aws": "aws-bedrock",
    "azure-ai-foundry": "azure-foundry",
    "code-assist": "google-oauth",
    "custom-direct": "custom-direct-api",
    "google-gemini-oauth-code-assist": "google-oauth",
    "google-gemini-via-oauth-code-assist": "google-oauth",
    "google": "google-ai-studio",
    "hugging-face-inference-providers": "huggingface",
    "huggingface-inference-providers": "huggingface",
    "kimi": "kimi-coding-plan",
    "kilo": "kilo-code",
    "kimi-moonshot-api": "moonshot-api",
    "lmstudio": "lm-studio",
    "minimax": "minimax-global",
    "minimax-via-oauth-browser-login": "minimax-oauth",
    "moonshot": "moonshot-api",
    "moonshotai": "moonshot-api",
    "nvidia-nim": "nvidia-nim",
    "nvidia": "nvidia-nim",
    "nous-research-subscription": "nous-portal",
    "openai-codex": "openai-codex",
    "openai": "openai-api",
    "github-copilot": "github-copilot",
    "github-copilot-acp": "github-copilot-acp",
    "opencode-go-10-month-subscription": "opencode-go",
    "dashscope": "qwen-cloud",
    "qwen-cloud-dashscope-coding": "qwen-cloud",
    "qwen-dashscope": "qwen-cloud",
    "tencent": "tencent-tokenhub",
    "tokenhub": "tencent-tokenhub",
    "tencent-tokenhub": "tencent-tokenhub",
    "xiaomi-mimo": "xiaomi",
    "xai-grok-oauth": "xai-oauth",
    "zai": "z-ai",
    "z-ai-glm": "z-ai",
    "zai-glm": "z-ai",
    "zhipuai": "z-ai",
    "glm": "z-ai",
    "mistral-nemo": "local",
    "qwen": "local",
    "phi4": "local",
    "nemotron": "local",
}


def get_provider_catalog():
    return [
        {
            **provider,
            "economicLabel": ECONOMIC_CLASS_LABELS[provider["economicClass"]],
        }
        for provider in HERMES_PROVIDER_CATALOG
    ]


def normalize_provider(provider):
    """Normalize Hermes provider identifiers into stable taxonomy keys."""
    normalized = (provider or "").strip().lower()
    if not normalized:
        return "unknown"

    normalized = re.sub(r"[\s_/.]+", "-", normalized)
    normalized = re.sub(r"[^a-z0-9-]+", "", normalized).strip("-")
    if not normalized:
        return "unknown"

    if normalized in PROVIDER_ALIASES:
        return PROVIDER_ALIASES[normalized]

    for prefix, alias in PROVIDER_ALIASES.items():
        if normalized.startswith(prefix):
            return alias

    return normalized


def classify_provider_economic_class(provider):
    provider_key = normalize_provider(provider)
    if provider_key in USAGE_BILLABLE_PROVIDERS:
        return "usage_billable"
    if provider_key in SUBSCRIPTION_PROVIDERS:
        return "subscription_based"
    if provider_key in OSS_PROVIDERS:
        return "oss"
    return "unknown"


def classify_session_economic_class(session):
    return classify_provider_economic_class(session.get("billing_provider"))


def build_economic_breakdown(provider_rows):
    totals = {class_key: 0 for class_key in ECONOMIC_CLASS_ORDER}
    for row in provider_rows:
        class_key = row.get("economicClass") or classify_session_economic_class(row)
        if class_key not in totals:
            class_key = "unknown"
        totals[class_key] += row.get("total_tokens", 0) or 0

    return [
        {
            "class": class_key,
            "label": ECONOMIC_CLASS_LABELS[class_key],
            "tokens": totals[class_key],
        }
        for class_key in ECONOMIC_CLASS_ORDER
    ]


def build_provider_usage_breakdown(provider_rows):
    usage = []
    for row in provider_rows:
        provider_key = normalize_provider(row.get("billing_provider"))
        class_key = row.get("economicClass") or classify_provider_economic_class(provider_key)
        catalog_entry = PROVIDER_CATALOG_BY_KEY.get(provider_key)
        raw_provider = row.get("billing_provider") or "unknown"
        raw_label = str(raw_provider).replace("-", " ").title()
        label = catalog_entry["label"] if catalog_entry else f"{raw_label} / unclassified"
        models = [
            model.strip()
            for model in (row.get("models") or "").split(",")
            if model and model.strip()
        ]

        usage.append({
            "provider": provider_key,
            "label": label,
            "economicClass": class_key,
            "economicLabel": ECONOMIC_CLASS_LABELS.get(class_key, ECONOMIC_CLASS_LABELS["unknown"]),
            "tokens": row.get("total_tokens", 0) or 0,
            "sessions": row.get("session_count", 0) or 0,
            "models": models,
        })

    return sorted(usage, key=lambda item: item["tokens"], reverse=True)
