import discord
from discord.ext import commands
import asyncio
import re
from config import DISCORD_TOKEN, DEFAULT_MODEL
from openrouter import ask_openrouter, ask_openrouter_with_image_url, fetch_url_content, download_image_to_base64

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.current_model = DEFAULT_MODEL

# Store per-channel history
channel_history: dict[int, list[dict]] = {}

# URL regex pattern
URL_PATTERN = re.compile(r'https?://[^\s]+')


@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")
    print(f"   Serving {len(bot.guilds)} guild(s)")
    
    # Load cogs
    await bot.load_extension("cogs.ai")
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"   Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"   ⚠️ Failed to sync commands: {e}")


@bot.event
async def on_message(message: discord.Message):
    # Ignore own messages
    if message.author == bot.user:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Respond to @mentions
    if bot.user in message.mentions:
        question = message.content
        
        # Remove mentions from the message
        for mention in message.mentions:
            question = question.replace(mention.mention, "").strip()
        
        # Check if message is a reply to another message
        original_attachment = None
        original_url = None
        referenced_msg = None
        referenced_context = ""
        if message.reference:
            try:
                ref = message.reference
                referenced_msg = await message.channel.fetch_message(ref.message_id)
                
                # Check attachments first
                if referenced_msg.attachments:
                    for att in referenced_msg.attachments:
                        if att.content_type and att.content_type.startswith('image/'):
                            original_attachment = await download_image_to_base64(att.url)
                            break
                
                # Check embeds (for images from URLs like Twitter)
                if not original_attachment and referenced_msg.embeds:
                    for embed in referenced_msg.embeds:
                        if embed.image and embed.image.url:
                            original_url = embed.image.url
                            break
                        elif embed.thumbnail and embed.thumbnail.url:
                            original_url = embed.thumbnail.url
                            break
                
                # Build referenced_context: URLs and link embeds from replied-to message
                ref_urls = URL_PATTERN.findall(referenced_msg.content or "")
                if ref_urls or any(getattr(e, "url", None) for e in (referenced_msg.embeds or [])):
                    await message.channel.typing()
                for url in ref_urls[:2]:
                    content = await fetch_url_content(url)
                    referenced_context += f"\n\n[{url}]\n{content}"
                embed_count = 0
                for embed in referenced_msg.embeds or []:
                    if embed_count >= 2:
                        break
                    if getattr(embed, "url", None):
                        if embed.title or embed.description:
                            referenced_context += f"\n\n[{embed.url}]\nTitle: {embed.title or ''}\n{embed.description or ''}"
                        else:
                            content = await fetch_url_content(embed.url)
                            referenced_context += f"\n\n[{embed.url}]\n{content}"
                        embed_count += 1
                            
            except Exception as e:
                referenced_msg = None
        
        # Check for image attachments in current message
        image_b64 = None
        image_url = None
        if message.attachments:
            for att in message.attachments:
                if att.content_type and att.content_type.startswith('image/'):
                    image_b64 = await download_image_to_base64(att.url)
                    break
        
        # Check current message embeds too
        if not image_b64 and not image_url and message.embeds:
            for embed in message.embeds:
                if embed.image and embed.image.url:
                    image_url = embed.image.url
                    break
                elif embed.thumbnail and embed.thumbnail.url:
                    image_url = embed.thumbnail.url
                    break
        
        # Use original message's image if current message has no image
        if not image_b64 and not image_url:
            if original_attachment:
                image_b64 = original_attachment
            elif original_url:
                image_url = original_url
        
        if not question.strip():
            # Check for attachments (images) in current or referenced message
            if image_b64 or image_url or message.attachments or original_attachment:
                await message.channel.typing()
                try:
                    img_to_use = image_b64 or image_url
                    prompt = "Apa yang kamu lihat di gambar ini?"
                    
                    if image_url:
                        response = await ask_openrouter_with_image_url(
                            prompt,
                            bot.current_model,
                            image_url=img_to_use
                        )
                    else:
                        response = await ask_openrouter(
                            prompt,
                            bot.current_model,
                            image_url=img_to_use
                        )
                    
                    if response:
                        await message.reply(response)
                    else:
                        await message.reply("⚠️ Gagal download gambar.")
                    return
                except Exception as e:
                    await message.reply(f"⚠️ Error: {str(e)}")
                    return
            
            # Reply with only mention to URL/embed: use referenced context
            if referenced_context.strip():
                final_question = "Berikut konten yang Kak kirim. Jelaskan atau rangkum isinya." + referenced_context
                async with message.channel.typing():
                    history = channel_history.get(message.channel.id, [])
                    try:
                        response = await ask_openrouter(
                            final_question,
                            bot.current_model,
                            history
                        )
                        if message.channel.id not in channel_history:
                            channel_history[message.channel.id] = []
                        channel_history[message.channel.id].append({"role": "user", "content": final_question})
                        channel_history[message.channel.id].append({"role": "assistant", "content": response})
                        if len(channel_history[message.channel.id]) > 20:
                            channel_history[message.channel.id] = channel_history[message.channel.id][-20:]
                        if len(response) <= 2000:
                            await message.reply(response)
                        else:
                            chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                            for i, chunk in enumerate(chunks):
                                await (message.reply(chunk) if i == 0 else message.channel.send(chunk))
                                await asyncio.sleep(0.5)
                        return
                    except Exception as e:
                        await message.reply(f"⚠️ Error: {str(e)}")
                        return
            
            # No question, no image, no referenced context
            await message.reply("Ada apa Kak?")
            return
        
        # Check for URLs in the message (current + referenced already in referenced_context)
        urls = URL_PATTERN.findall(message.content)
        url_content = ""
        if urls:
            for url in urls[:2]:
                content = await fetch_url_content(url)
                url_content += f"\n\n[{url}]\n{content}"
        
        # Build final question with URL content and referenced context
        final_question = question
        if url_content:
            final_question = f"{question}\n\nBerikut isi dari URL yang Kak kirim:{url_content}"
        if referenced_context.strip():
            final_question = f"{final_question}\n\nKonteks dari pesan yang di-reply:{referenced_context}"
        
        async with message.channel.typing():
            history = channel_history.get(message.channel.id, [])
            try:
                response = await ask_openrouter(
                    final_question,
                    bot.current_model,
                    history,
                    image_url=image_b64 or image_url
                )
                
                # Save to history
                if message.channel.id not in channel_history:
                    channel_history[message.channel.id] = []
                
                channel_history[message.channel.id].append(
                    {"role": "user", "content": final_question}
                )
                channel_history[message.channel.id].append(
                    {"role": "assistant", "content": response}
                )
                
                # Trim history
                if len(channel_history[message.channel.id]) > 20:
                    channel_history[message.channel.id] = channel_history[message.channel.id][-20:]
                
                # Split if too long
                if len(response) <= 2000:
                    await message.reply(response)
                else:
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            await message.channel.send(chunk)
                        await asyncio.sleep(0.5)
                        
            except Exception as e:
                await message.reply(f"⚠️ Error: {str(e)}")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("⚠️ DISCORD_TOKEN not set. Copy .env.example to .env and fill in your tokens.")
    else:
        bot.run(DISCORD_TOKEN)
