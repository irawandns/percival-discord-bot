# Percival Discord Bot

An AI-powered Discord bot that uses OpenRouter to answer questions.

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your tokens
3. Install dependencies: `uv sync`
4. Run: `uv run python bot.py`

## Commands

- `/ask <question>` — Ask anything
- `/model [name]` — Switch or view current model
- `/clear` — Clear conversation history
- `/help` — Show available commands

## Features

- **@mention chat** — Mention the bot to get a response
- **Reply-to-context** — Reply to a message (image, URL, or link embed) and mention the bot; it responds using that message's context
- **Slash commands** — Clean `/ask` interface
- **Model switching** — Choose any OpenRouter model
- **Streaming** — Real-time response typing
- **Conversation memory** — Per-channel context

## Powered by

- [discord.py](https://github.com/Rapptz/discord.py)
- [OpenRouter](https://openrouter.ai)
