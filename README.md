# Percival Discord Bot

An AI-powered Discord bot that uses OpenRouter to answer questions.

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your tokens
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python bot.py`

## Commands

- `/ask <question>` — Ask anything
- `/model [name]` — Switch or view current model
- `/clear` — Clear conversation history
- `/help` — Show available commands

## Features

- **@mention chat** — Mention the bot to get a response
- **Slash commands** — Clean `/ask` interface
- **Model switching** — Choose any OpenRouter model
- **Streaming** — Real-time response typing
- **Conversation memory** — Per-channel context

## Powered by

- [discord.py](https://github.com/Rapptz/discord.py)
- [OpenRouter](https://openrouter.ai)
