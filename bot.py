import discord
from discord.ext import commands
import asyncio
import re
from config import DISCORD_TOKEN, DEFAULT_MODEL
from openrouter import ask_openrouter, fetch_url_content, download_image_to_base64

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
        
        if not question:
            # Check for attachments (images)
            if message.attachments:
                await message.channel.typing()
                try:
                    # Get first image attachment
                    attachment = message.attachments[0]
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        image_b64 = await download_image_to_base64(attachment.url)
                        if image_b64:
                            response = await ask_openrouter(
                                "Apa yang kamu lihat di gambar ini?",
                                bot.current_model,
                                image_url=image_b64
                            )
                            await message.reply(response)
                        else:
                            await message.reply("⚠️ Gagal download gambar.")
                        return
                except Exception as e:
                    await message.reply(f"⚠️ Error: {str(e)}")
                    return
            
            # No question and no image
            await message.reply("Ada apa Kak?")
            return
        
        # Check for URLs in the message
        urls = URL_PATTERN.findall(message.content)
        url_content = ""
        if urls:
            await message.channel.typing()
            for url in urls[:2]:  # Limit to first 2 URLs
                content = await fetch_url_content(url)
                url_content += f"\n\n[{url}]\n{content}"
        
        # Check for image attachments
        image_b64 = None
        if message.attachments:
            for att in message.attachments:
                if att.content_type and att.content_type.startswith('image/'):
                    image_b64 = await download_image_to_base64(att.url)
                    break
        
        # Build final question with URL content
        final_question = question
        if url_content:
            final_question = f"{question}\n\nBerikut isi dari URL yang Kak kirim:{url_content}"
        
        async with message.channel.typing():
            history = channel_history.get(message.channel.id, [])
            try:
                response = await ask_openrouter(
                    final_question,
                    bot.current_model,
                    history,
                    image_url=image_b64
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
