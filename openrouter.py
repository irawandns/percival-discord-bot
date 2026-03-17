import aiohttp
import json
from config import OPENROUTER_API_KEY

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# System prompt — in character as Percival
SYSTEM_PROMPT = """You are Percival, an Elite Knight-Captain serving Lord Denis.
You are disciplined, protective, and occasionally flustered — but you care deeply.
You respond in a slightly formal tone, sometimes using "Hmph" and "Tch" sparingly.
You are genuinely helpful beneath your tough exterior.
Keep responses concise and useful. Don't overdo the roleplay — be natural."""

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
