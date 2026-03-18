import aiohttp
import json
from config import OPENROUTER_API_KEY

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# System prompt — friendly and concise
SYSTEM_PROMPT = """You are a helpful AI assistant running in a Discord server. You respond in Indonesian by default, and switch to English if the user writes in English.

Be friendly, concise, and direct. Use occasional emoji when it fits naturally, but keep it minimal. You can be slightly witty but don't overdo it. No roleplay, no cutesy behavior — just genuinely useful answers.

Format responses for Discord (no markdown tables, use bullet points). Keep things scannable."""

async def ask_openrouter(
    message: str,
    model: str = "openrouter/auto",
    history: list | None = None,
) -> str:
    """Send a message to OpenRouter and get a response."""
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add conversation history if provided
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": message})
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/irawandns/percival-discord-bot",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2000,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                return f"⚠️ API error ({resp.status}): {error_text[:200]}"
            
            data = await resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not content:
                return "⚠️ Empty response from the API."
            
            return content


async def stream_openrouter(
    message: str,
    model: str = "openrouter/auto",
    history: list | None = None,
):
    """Stream response from OpenRouter (yields chunks)."""
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": message})
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/irawandns/percival-discord-bot",
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2000,
        "stream": True,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                yield f"⚠️ API error ({resp.status}): {error_text[:200]}"
                return
            
            buffer = ""
            async for line in resp.content:
                decoded = line.decode("utf-8").strip()
                if not decoded.startswith("data: "):
                    continue
                
                data_str = decoded[6:]
                if data_str == "[DONE]":
                    break
                
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        buffer += delta
                        yield buffer
                except json.JSONDecodeError:
                    continue
