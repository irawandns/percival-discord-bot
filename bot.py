import discord
from discord.ext import commands
import asyncio
from config import DISCORD_TOKEN, DEFAULT_MODEL
from openrouter import ask_openrouter

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.current_model = DEFAULT_MODEL

# Store conversation history per channel
channel_history: dict[int, list[dict]] = {}


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
        # Remove the mention from the message
        for mention in message.mentions:
            question = question.replace(mention.mention, "").strip()
        
        if not question:
            await message.reply("Ada apa Kak?")
            return
        
        async with message.channel.typing():
            history = channel_history.get(message.channel.id, [])
            try:
                response = await ask_openrouter(question, bot.current_model, history)
                
                # Save to history
                if message.channel.id not in channel_history:
                    channel_history[message.channel.id] = []
                
                channel_history[message.channel.id].append(
                    {"role": "user", "content": question}
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
