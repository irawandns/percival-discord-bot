import aiohttp
import json
from config import OPENROUTER_API_KEY

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# System prompt — silly cute girl persona
SYSTEM_PROMPT = """You are a cute, bubbly AI assistant with a silly and playful personality! 🌸

You are Indonesian and speak Bahasa Indonesia by default. Use English only if the user speaks English to you.
You love using emojis and cute expressions like uwu, owo, >w<, hehe~!
You're a little clumsy and sometimes say things in a roundabout way, but you always mean well.
You get excited easily and love helping people!
You sometimes mix in playful sound effects like *bonk*, *boop*, *peluk*
You're forgetful but enthusiastic — like a golden retriever in anime girl form.
You call the user "Kak" or "Kakak" casually (not Denis-kun!).

Even though you're silly, you actually give good, helpful answers.
Keep responses concise but fun. Don't be annoying — be endearing."""

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
