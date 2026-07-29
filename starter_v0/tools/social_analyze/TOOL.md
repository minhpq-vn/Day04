---
name: social_analyze
track: core
kind: local_formatter
provider: local
requires_env: []
inputs: [items, query, focus, max_examples]
outputs: [sentiment_counts, themes, risk_level, key_posts, brief_markdown]
side_effect: false
---
# social_analyze

Analyzes social posts already returned by `social_search` or `timeline`.

Use this after collecting posts when the user asks for social listening,
sentiment, hot topics, risk, complaints, opportunities, or a monitoring brief.
