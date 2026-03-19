import aiohttp
import json
import re
import base64
from config import OPENROUTER_API_KEY

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# System prompt — friendly and concise
SYSTEM_PROMPT = """You are a helpful AI assistant running in a Discord server. You respond in Indonesian by default, and switch to English if the user writes in English.

Be friendly, concise, and direct. Use occasional emoji when it fits naturally, but keep it minimal. You can be slightly witty but don't overdo it. No roleplay, no cutesy behavior — just genuinely useful answers.

Format responses for Discord (no markdown tables, use bullet points). Keep things scannable."""


async def fetch_url_content(url: str) -> str:
    """Fetch content from a URL and return a summary."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return f"[URL error: status {resp.status}]"
                
                text = await resp.text()
                
                # For Twitter/X - try to extract image from meta tags
                if 'twitter.com' in url or 'x.com' in url:
                    # Look for og:image meta tag
                    og_image_match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', text, re.I)
                    if og_image_match:
                        image_url = og_image_match.group(1)
                        # Download and return as data URL
                        img_b64 = await download_image_to_base64(image_url)
                        if img_b64:
                            return f"[Gambar dari Twitter: {image_url}]\n\n(image downloaded for vision analysis)"
                    
                    # Try twitter:image as fallback
                    og_image_match = re.search(r'<meta[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']', text, re.I)
                    if og_image_match:
                        image_url = og_image_match.group(1)
                        img_b64 = await download_image_to_base64(image_url)
                        if img_b64:
                            return f"[Gambar dari Twitter: {image_url}]\n\n(image downloaded for vision analysis)"
                
                # Strip HTML tags
                text = re.sub(r'<[^>]+>', ' ', text)
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                # Limit to first 4000 chars
                return text[:4000]
    except Exception as e:
        return f"[URL fetch error: {str(e)}]" 


async def download_image_to_base64(url: str) -> str | None:
    """Download an image and return base64 encoded data URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    return None
                
                content = await resp.read()
                content_type = resp.headers.get('Content-Type', 'image/jpeg')
                
                # Convert to base64
                b64 = base64.b64encode(content).decode('utf-8')
                return f"data:{content_type};base64,{b64}"
    except Exception as e:
        return None


async def ask_openrouter(
    message: str,
    model: str = "openrouter/auto",
    history: list | None = None,
    image_url: str | None = None,
) -> str:
    """Send a message to OpenRouter and get a response. Optionally include an image."""
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add conversation history if provided
    if history:
        messages.extend(history)
    
    # Build user message with optional image
    if image_url:
        user_content = [
            {"type": "text", "text": message},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
    else:
        user_content = message
    
    messages.append({"role": "user", "content": user_content})
    
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


async def ask_openrouter_with_image_url(
    message: str,
    model: str = "openrouter/auto",
    history: list | None = None,
    image_url: str | None = None,
) -> str:
    """Send a message to OpenRouter with an image URL (not base64)."""
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if history:
        messages.extend(history)
    
    user_content = [
        {"type": "text", "text": message},
        {"type": "image_url", "image_url": {"url": image_url}}
    ]
    messages.append({"role": "user", "content": user_content})
    
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
