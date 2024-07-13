import discord
from discord import DiscordException, app_commands
from discord.ui import Button, View
from discord.ext import commands
import dotenv
import json
import os
dotenv.load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
activity = discord.Game(name="Hosting Quizzes..")
bot = commands.Bot(command_prefix="$", intents=intents, activity=activity)
client = bot
with open('questions.json') as f:
    questions = json.load(f)

current_question = None
score = {}


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await bot.tree.sync()


@client.event
async def on_message(message):
    if message.author == client.user:
        return


@bot.hybrid_command(name="question", description="Asks a Question from the set.")
@app_commands.describe(type="Type of question")
async def ask_question(ctx, type: str):
    global current_question
    for question in questions:
        if question['type'] == type:
            current_question = question
            break
    embed = discord.Embed(
        title="Question",
        description=current_question['question'],
        color=discord.Color.blue()
    )

    QuestionView = View()
    QuestionView.add_item(
        Button(label="Answer", style=discord.ButtonStyle.primary))

    await ctx.send(embed=embed, view=QuestionView)
    # await ctx.send("Type /answer to answer the question.")


client.run(os.getenv('TOKEN'))
