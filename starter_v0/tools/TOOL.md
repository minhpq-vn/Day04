# Tools for Social Listening Monitor

This document summarizes the tools available to the agent and how they should be used for the Social Listening Monitor project.

## Core Workflow

Typical flow:

1. Use `social_search` or `timeline` to collect social posts.
2. Use `social_analyze` to analyze the collected posts.
3. Use `format` when the user wants a digest, report, bullet list, or thread.
4. Use `lookup` or `fetch` only when web/news context or a specific URL is needed.
5. Use `clarify` when required information is missing.
6. Use `send` only after explicit user confirmation.

## Tool List

| Tool | Purpose | When to use |
|---|---|---|
| `clarify` | Ask the user for missing information or confirmation. | Use when a request lacks a required target, URL, account, or when an action needs confirmation. |
| `timeline` | Fetch recent posts from one specific Twitter/X account. | Use for requests like "latest tweets from Elon Musk" or "recent posts from @sama". |
| `social_search` | Search Twitter/X posts by keyword. | Use for brand, product, hashtag, event, topic, competitor, or "what are people saying about..." requests. |
| `social_analyze` | Analyze collected social posts. | Use after `social_search` or `timeline` when the user wants sentiment, hot topics, complaints, risks, opportunities, or a monitoring brief. |
| `lookup` | Search the web or news. | Use for non-social news, background research, verification, or cross-checking public context. |
| `fetch` | Read content from a specific URL. | Use only when the user provides a URL to summarize or inspect. |
| `format` | Convert collected items into a readable output. | Use for briefs, sections, bullet lists, threads, or daily digests. |
| `policy` | Search internal company policy documents. | Use for privacy, citation, publishing, AI research, or tool usage policy questions. |
| `send` | Send a prepared message externally. | Use only after explicit yes/no confirmation from the user. |
| `papers` | Search scientific papers. | Use for research-paper discovery, not for normal social listening unless the topic requires academic sources. |
| `paper_text` | Extract text from an arXiv paper. | Use after `papers` or when the user gives an arXiv URL/ID. |

## Social Listening Routing Rules

Use `social_search` when the user asks:

- "What are people saying about X?"
- "Find tweets about X."
- "Any complaints about X?"
- "What is hot on Twitter/X about X?"
- "Monitor this hashtag."

Use `search_type="Latest"` for:

- recent posts
- latest updates
- "today"
- "dao nay"
- early monitoring during an incident

Use `search_type="Top"` for:

- hot posts
- viral posts
- trending discussions
- popular tweets
- high-impact posts

Use `timeline` when the target is a specific account:

- "latest tweets from Sam Altman"
- "recent posts by @OpenAI"
- "what did Elon Musk tweet?"

Use `social_analyze` after posts are collected if the user asks for:

- sentiment
- complaints
- risks
- hot topics
- key posts
- summary brief
- PR recommendation
- social listening report

## Recommended Tool Chains

### Hot Topics on Twitter/X

User:

```text
What is hot on Twitter about OpenAI?
```

Tool chain:

```text
social_search(query="OpenAI", search_type="Top", limit=5)
social_analyze(items=<social_search.items>, query="OpenAI", focus="hot topics")
```

### Recent Brand Monitoring

User:

```text
Monitor recent complaints about VinFast.
```

Tool chain:

```text
social_search(query="VinFast complaint OR issue OR problem", search_type="Latest", limit=10)
social_analyze(items=<social_search.items>, query="VinFast", focus="complaints and risk")
```

### Account Timeline

User:

```text
Summarize the latest 5 tweets from Sam Altman.
```

Tool chain:

```text
timeline(screenname="sama", limit=5)
social_analyze(items=<timeline.items>, query="sama", focus="recent account activity")
```

### Social and Web Context

User:

```text
What are people saying about GPT-5 on Twitter, and is there related news?
```

Tool chain:

```text
social_search(query="GPT-5", search_type="Latest", limit=5)
lookup(query="GPT-5", topic="news", timeframe="week", max_results=5)
social_analyze(items=<social_search.items>, query="GPT-5", focus="social reaction")
```

## Guardrails

- Do not claim the results represent all of Twitter/X. Say the analysis is based on retrieved posts.
- Do not infer private data, demographics, or personal attributes.
- Do not send, publish, or post content without explicit confirmation.
- Ask for clarification when the account, URL, or monitoring target is missing.
- Prefer source-backed summaries with links when available.
- Separate observed signals from interpretation.
- For risk or sentiment, use cautious phrasing such as "signals suggest" or "from this sample".

## Minimum Tool Set for the Project

The minimum useful Social Listening Monitor requires:

- `social_search`
- `timeline`
- `social_analyze`
- `format`
- `clarify`

The recommended full project also uses:

- `lookup`
- `fetch`
- `policy`
- `send`

Academic tools are optional and not central to this project:

- `papers`
- `paper_text`
