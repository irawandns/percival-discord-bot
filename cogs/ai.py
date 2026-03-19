import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from config import DEFAULT_MODEL
from openrouter import ask_openrouter

# Store per-channel conversation history
channel_history: dict[int, list[dict]] = {}
MAX_HISTORY = 20  # Keep last 20 messages per channel

# Available models for quick switching
MODELS = {
    "auto": "openrouter/auto",
    "gpt4": "openai/gpt-4o",
    "claude": "anthropic/claude-sonnet-4",
    "gemini": "google/gemini-2.5-flash-preview",
    "llama": "meta-llama/llama-4-maverick",
}

class AI(commands.Cog):
    """AI chat commands powered by OpenRouter."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.current_model = DEFAULT_MODEL
    
    @app_commands.command(name="ask", description="Ask Percival anything")
    @app_commands.describe(question="Your question")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        
        # Build history for this channel
        history = channel_history.get(interaction.channel.id, [])
        
        try:
            response = await ask_openrouter(question, self.current_model, history)
            
            # Save to history
            if interaction.channel.id not in channel_history:
                channel_history[interaction.channel.id] = []
            
            channel_history[interaction.channel.id].append(
                {"role": "user", "content": question}
            )
            channel_history[interaction.channel.id].append(
                {"role": "assistant", "content": response}
            )
            
            # Trim history
            if len(channel_history[interaction.channel.id]) > MAX_HISTORY:
                channel_history[interaction.channel.id] = channel_history[interaction.channel.id][-MAX_HISTORY:]
            
            # Split long messages (Discord limit: 2000 chars)
            if len(response) <= 2000:
                await interaction.followup.send(response)
            else:
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await interaction.followup.send(chunk)
                    await asyncio.sleep(0.5)
                    
        except Exception as e:
            await interaction.followup.send(f"⚠️ Something went wrong: {str(e)}")
    
    @app_commands.command(name="model", description="Switch or view the current AI model")
    @app_commands.describe(name="Model name (e.g., auto, gpt4, claude, gemini)")
    async def model(self, interaction: discord.Interaction, name: str | None = None):
        if name is None:
            available = ", ".join(f"`{k}`" for k in MODELS.keys())
            await interaction.response.send_message(
                f"**Current model:** `{self.current_model}`\n"
                f"**Available:** {available}\n"
                f"Or paste a full OpenRouter model ID."
            )
            return
        
        # Check if it's a preset or custom model
        if name.lower() in MODELS:
            self.current_model = MODELS[name.lower()]
            await interaction.response.send_message(f"✅ Model switched to `{self.current_model}`")
        else:
            self.current_model = name
            await interaction.response.send_message(f"✅ Model set to `{self.current_model}`")
    
    @app_commands.command(name="clear", description="Clear conversation history for this channel")
    async def clear(self, interaction: discord.Interaction):
        channel_history.pop(interaction.channel.id, None)
        await interaction.response.send_message("🧹 Histori percakapan dihapus.")
    
    @app_commands.command(name="help", description="Show available commands")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚔️ Percival — Available Commands",
            color=discord.Color.gold(),
        )
        embed.add_field(name="/ask <question>", value="Ask me anything", inline=False)
        embed.add_field(name="/model [name]", value="Switch AI model (auto, gpt4, claude, gemini, llama)", inline=False)
        embed.add_field(name="/clear", value="Clear conversation history", inline=False)
        embed.add_field(name="@Percival", value="Mention me in chat, or reply to an image/URL/embed and mention me to respond with that context", inline=False)
        embed.set_footer(text="Tanya apa aja, aku bantu!")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
