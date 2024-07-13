import discord
from discord import app_commands
from discord.ui import Button, View
from discord.ext import commands
import dotenv
import json
import os
from Levenshtein import distance

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
answered = {}

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await bot.tree.sync()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

wrong_embed = discord.Embed(
    title="Wrong Answer", description="Your answer is WRONG!", color=discord.Color.red()
)
correct_embed = discord.Embed(
    title="Correct Answer", description="Your answer is RIGHT!", color=discord.Color.green()
)
already_answered = discord.Embed(
    title="Already Answered", description="You have already answered this question!", color=discord.Color.red()
)
question_closed = discord.Embed(
    title="Question Closed", description="This question has already been answered correctly.", color=discord.Color.red()
)

class QuestionView(View):
    def __init__(self, question):
        super().__init__(timeout=180.0)
        self.question = question
        self.message = None  # Initialize the message attribute

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def answer_check(self, interaction: discord.Interaction):
        if interaction.user.id in answered:
            await interaction.response.send_message(embed=already_answered, ephemeral=True)
            return
        answered[interaction.user.id] = True
        if interaction.data['custom_id'] == self.question['answer']:
            await interaction.response.send_message(embed=correct_embed, ephemeral=True)
            await self.close_question(interaction)
        else:
            wrong_embed.add_field(
                name="The Correct Answer is:", value=self.question['answer'])
            await interaction.response.send_message(embed=wrong_embed, ephemeral=True)

    async def close_question(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)
        current_question = None  # Reset the current question

@bot.hybrid_command(name="question", description="Asks a Question from the set.")
@app_commands.describe(ques_type="Type of question")
async def ask_question(ctx, ques_type: str):
    global current_question
    for question in questions:
        if question['type'] == ques_type:
            current_question = question
            break
    question_text = current_question["question"]

    if ques_type == "mcq":
        global answered
        answered = {}
        view = QuestionView(current_question)
        embed = discord.Embed(
            title="Question", description=question_text, color=discord.Color.greyple())

        for answer in current_question["options"]:
            btn = Button(
                label=answer, style=discord.ButtonStyle.primary, custom_id=answer)
            btn.callback = view.answer_check
            view.add_item(btn)

        message = await ctx.send(embed=embed, view=view)
        view.message = message  # Save the message object to the view for editing
    elif ques_type == "guess":
        embed = discord.Embed(
            title="Question", description=question_text, color=discord.Color.greyple())
        await ctx.send(embed=embed)

@bot.hybrid_command(name="answer", description="Submit your Answer to the question")
@app_commands.describe(ans="Answer to the question")
async def submit_answer(ctx, ans: str):
    global current_question
    if current_question["type"] == "guess":
        guess = ans.lower()
        correct = current_question["answer"].lower()
        if distance(guess, correct) <= 2:
            correct_embed.add_field(
                name=f"{ctx.author}'s Answer:", value=ans)
            await ctx.send(embed=correct_embed)
            current_question = None
        else:
            wrong_embed.add_field(
                name=f"{ctx.author}'s Answer:", value=ans)
            await ctx.send(embed=wrong_embed)
    else:
        await ctx.send("This command is only for Guess type questions.")


client.run(os.getenv('TOKEN'))
