# Percival Discord Bot — Future Features

## Priority 1 (Important)
- [ ] **URL fetching in messages** — Detect URLs, fetch content, include in AI prompt
- [ ] **Image/media support** — Accept image attachments, send to vision model
- [ ] **Per-user conversation history** — Each user should have their own history, not shared per channel
- [ ] **Per-user rate limiting** — e.g., 5 asks per minute per person to prevent abuse
- [ ] **OpenRouter rate limit handling** — Retry with backoff when API returns 429

## Priority 2 (Nice to have)
- [ ] **Streaming responses** — Show typing indicator and stream token-by-token (partially implemented in openrouter.py)
- [ ] **Conversation reset per user** — `/clear` should clear per-user history, not entire channel
- [ ] **Image support** — Allow uploading images with `/ask` for vision models
- [ ] **Persistent memory** — Save conversation history to a file/DB so it survives restarts

## Priority 3 (Future)
- [ ] **Custom system prompts per channel** — Different personalities per channel
- [ ] **Voice support** — TTS responses using ElevenLabs (sag skill)
- [ ] **Web dashboard** — Monitor bot usage, stats, manage settings
- [ ] **Plugin system** — Let users add custom skills/tools to the bot

## Notes
- Bot is currently running via `nohup python bot.py` on the server
- Repo: https://github.com/irawandns/percival-discord-bot
