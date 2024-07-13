import discord
from discord.ui import Button, View
from discord.ext import commands
import dotenv
import json
import os
dotenv.load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
activity = discord.Game(name="WT20 2024 Fantasy Auction")
bot = commands.Bot(command_prefix="&", intents=intents, activity=activity)
client = bot
with open('questions.json') as f:
    questions = json.load(f)

current_question = None
score = {}


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    global current_question
    global score

    if message.content.startswith('$quiz'):
        if not current_question:
            current_question = questions[0]
            await message.channel.send(current_question['question'])
            if 'options' in current_question:
                for i, option in enumerate(current_question['options']):
                    await message.channel.send(f"{i+1}. {option}")
        else:
            await message.channel.send("Quiz already in progress!")

    elif current_question:
        if current_question['type'] == 'multiple_choice':
            answer = current_question['options'][int(message.content) - 1]
        elif current_question['type'] == 'true_false':
            answer = message.content.lower() in ['true', 'yes', 'y']

        if answer == current_question['answer']:
            score[message.author] = score.get(message.author, 0) + 1
            await message.channel.send(f"Correct! Your score is {score[message.author]}")
        else:
            await message.channel.send("Incorrect!")

        current_question = None

client.run(os.getenv('TOKEN'))
