import random
import discord
from discord import app_commands
from discord.ui import Button, View
from discord.ext import commands, tasks
import dotenv
import json
import os
from Levenshtein import distance
import asyncio  # Import asyncio for timers
import datetime

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
teams = {}
current_mode = None
start_time = None
total_time = 120
current_team = 0
rem_time = 0
team_order = []
pounced = []
correct_teams = []
wrong_teams = []
attempted = []
answered_right = []
asked = []
prelims_answers = []
team_answers = {}
WRONG_ANSWER_PENALTY = -1
CORRECT_ANSWER_POINTS = 2
CURRENT_TEAM_KEY = "current_team"
answered = {}  # Initialize answered dictionary


def pounce(team):
    global pounced
    timestamp = datetime.datetime.now()
    pounced.append((team, timestamp))


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await bot.tree.sync()
    await load()


@client.event
async def on_message(message):
    if message.author == client.user:
        await save()
        return
    if current_mode == "bounce_pounce":
        await handle_bounce_pounce(message)
    else:
        if current_question and current_question["type"] == "guess":
            await handle_guess_answer(message)
        elif current_question and current_question["type"] == "multi":
            await handle_multiple_answer(message)


async def load():
    # load all variables from a single json file:
    global questions, current_question, prelims_answers, total_time, team_answers, teams, current_mode, start_time, current_team, rem_time, team_order, pounced, asked, correct_teams, wrong_teams, attempted, WRONG_ANSWER_PENALTY, CORRECT_ANSWER_POINTS, answered

    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data/save1.json'):
        return
    with open('data/save1.json') as f:
        data = json.load(f)
        questions = data["questions"]
        current_question = data["current_question"]
        teams = data["teams"]
        current_mode = data["current_mode"]
        start_time = data["start_time"]
        current_team = data["current_team"]
        rem_time = data["rem_time"]
        team_order = data["team_order"]
        pounced = data["pounced"]
        correct_teams = data["correct_teams"]
        wrong_teams = data["wrong_teams"]
        attempted = data["attempted"]
        WRONG_ANSWER_PENALTY = data["WRONG_ANSWER_PENALTY"]
        CORRECT_ANSWER_POINTS = data["CORRECT_ANSWER_POINTS"]
        answered = data["answered"]
        asked = data["asked"]
        prelims_answers = data["prelims_answers"]
        team_answers = data["team_answers"]
        total_time = data["total_time"]
        print("loaded data")


async def save():
    # save all variables to a single json file:
    global questions, total_time, current_question, team_answers, teams, current_mode, start_time, current_team, rem_time, team_order, pounced, correct_teams, wrong_teams, attempted, WRONG_ANSWER_PENALTY, CORRECT_ANSWER_POINTS, answered
    # keep 5 save files, delete the oldest one and add the newest one:
    # if no save files exist:
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists('data/save1.json'):
        for i in range(1, 6):
            with open(f'data/save{i}.json', 'w') as f:
                json.dump({
                    "questions": questions,
                    "current_question": current_question,
                    "teams": teams,
                    "current_mode": current_mode,
                    "start_time": start_time,
                    "current_team": current_team,
                    "rem_time": rem_time,
                    "team_order": team_order,
                    "pounced": pounced,
                    "correct_teams": correct_teams,
                    "wrong_teams": wrong_teams,
                    "attempted": attempted,
                    "WRONG_ANSWER_PENALTY": WRONG_ANSWER_PENALTY,
                    "CORRECT_ANSWER_POINTS": CORRECT_ANSWER_POINTS,
                    "answered": answered,
                    "asked": asked,
                    "prelims_answers": prelims_answers,
                    "team_answers": team_answers,
                    "total_time": total_time
                }, f)
        return

    for i in range(4, 0, -1):
        os.rename(f'data/save{i}.json', f'data/save{i+1}.json')
    with open('data/save1.json', 'w') as f:
        json.dump({
            "questions": questions,
            "current_question": current_question,
            "teams": teams,
            "current_mode": current_mode,
            "start_time": start_time,
            "current_team": current_team,
            "rem_time": rem_time,
            "team_order": team_order,
            "pounced": pounced,
            "correct_teams": correct_teams,
            "wrong_teams": wrong_teams,
            "attempted": attempted,
            "WRONG_ANSWER_PENALTY": WRONG_ANSWER_PENALTY,
            "CORRECT_ANSWER_POINTS": CORRECT_ANSWER_POINTS,
            "answered": answered,
            "asked": asked,
            "prelims_answers": prelims_answers,
            "team_answers": team_answers,
            "total_time": total_time
        }, f)

# Embed declarations
wrong_embed = discord.Embed(
    title="Wrong Answer", description="Your answer is WRONG!", color=discord.Color.red())
correct_embed = discord.Embed(
    title="Correct Answer", description="Your answer is RIGHT!", color=discord.Color.green())
already_answered = discord.Embed(
    title="Already Answered", description="You have already answered this question!", color=discord.Color.red())
question_closed = discord.Embed(
    title="Question Closed", description="This question has already been answered correctly.", color=discord.Color.red())


class QuestionView(View):
    def __init__(self, question, mode):
        super().__init__(timeout=60.0)
        self.question = question
        self.mode = mode
        self.message = None
        self.muted = False

        if self.mode == "bounce_pounce":
            self.add_item(
                Button(label="Pounce", style=discord.ButtonStyle.success, custom_id="pounce"))
            self.add_item(
                Button(label="Bounce", style=discord.ButtonStyle.danger, custom_id="bounce"))

    async def on_timeout(self):
        for child in self.children:
            if child.label == "Pounce":
                child.disabled = True
                if self.message:
                    await self.message.edit(view=self)
            else:
                await asyncio.sleep(30)
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
            await self.update_score(interaction, correct=True)
            await self.close_question(interaction)
        else:
            wrong_embed.add_field(
                name="The Correct Answer is:", value=self.question['answer'])
            await interaction.response.send_message(embed=wrong_embed, ephemeral=True)
            await self.update_score(interaction, correct=False)
            if self.mode == "bounce_pounce":
                await self.bounce_question(interaction)

    async def close_question(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)
        global current_question
        current_question = None
        answered = {}

    async def update_score(self, interaction: discord.Interaction, correct: bool):
        team = teams[team_order[current_team]]
        if correct:
            team["score"] += CORRECT_ANSWER_POINTS
        else:
            team["score"] += WRONG_ANSWER_PENALTY
        await interaction.channel.send(f"Team {team_order[current_team]} now has {team['score']} points.")

    async def bounce_question(self, interaction: discord.Interaction):
        global current_team, attempted, current_question, current_mode, correct_teams, wrong_teams
        user = interaction.user.id
        for team in teams:
            if user in teams[team]["members"] and team == team_order[current_team]:
                await bounce_questions(interaction, self)
                return
        await interaction.response.send_message("You are not allowed to bounce the question.", ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        global rem_time
        if interaction.data['custom_id'] == "bounce":
            await self.bounce_question(interaction)
            return False
        elif interaction.data['custom_id'] == "pounce":
            user = interaction.user.id
            for team in teams:
                if user in teams[team]["members"]:
                    for team_, timestamp in pounced:
                        if team == team_:
                            await interaction.response.send_message(f"Team {team} has already pounced!", ephemeral=True)
                            return False
                    pounce(team)
                    rem_time = 60 - (pounced[-1][1] - start_time).seconds
                    await interaction.response.send_message(f"Team {team} has pounced! Answer using /answer. Remaining time = {rem_time} seconds", ephemeral=True)
                    attempted.append(team)
                    return True
            return True
        return True


@bot.hybrid_command(name="reset", description="Resets the quiz settings")
async def reset(ctx):
    global questions, team_answers, total_time, asked, prelims_answers, current_question, teams, current_mode, start_time, current_team, rem_time, team_order, pounced, correct_teams, wrong_teams, attempted, WRONG_ANSWER_PENALTY, CORRECT_ANSWER_POINTS, answered
    questions = []
    current_question = None
    teams = {}
    current_mode = None
    start_time = None
    current_team = 0
    rem_time = 0
    team_order = []
    pounced = []
    correct_teams = []
    wrong_teams = []
    attempted = []
    WRONG_ANSWER_PENALTY = -1
    CORRECT_ANSWER_POINTS = 2
    answered = {}
    asked = []
    prelims_answers = []
    team_answers = {}
    total_time = 120
    await save()
    await ctx.send("Quiz settings have been reset.")


@bot.hybrid_command(name="question", description="Asks a Question from the set.")
@app_commands.describe(ques_type="Type of question", mode="Mode of the question")
async def ask_question(ctx, ques_type: str, mode: str = None):
    global current_question, current_team, answered, current_mode
    current_mode = mode
    answered = {}
    question = random.choice(questions)
    # pick a random question:
    while question["type"] != ques_type:
        question = random.choice(questions)
    current_question = question
    current_question["channel_id"] = ctx.channel.id

    question_text = current_question["question"]

    if ques_type == "mcq":
        view = QuestionView(current_question, mode)
        embed = discord.Embed(
            title="Question", description=question_text, color=discord.Color.greyple())

        for answer in current_question["options"]:
            btn = Button(
                label=answer, style=discord.ButtonStyle.primary, custom_id=answer)
            btn.callback = view.answer_check
            view.add_item(btn)
        await save()
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    elif ques_type == "guess":
        embed = discord.Embed(
            title="Question", description=question_text, color=discord.Color.greyple())
        embed.add_field(name="Answer", value="Type your answer in the chat.")
        await ctx.send(embed=embed)
        if mode == "bounce_pounce":
            view = QuestionView(current_question, mode)
            crt = discord.Embed(title="Current Team", description=f"Team {
                                team_order[current_team]}", color=discord.Color.green())
            message = await ctx.send(embed=crt, view=view)
            view.message = message
            await save()
            await mute_current_team(ctx)
            await start_timers(ctx, view)
    elif ques_type == "multi":
        embed = discord.Embed(
            title="Question", description=question_text, color=discord.Color.greyple())
        await ctx.send(embed=embed)
        if mode == "bounce_pounce":
            view = QuestionView(current_question, mode)
            message = await ctx.send(view=view)
            view.message = message
            await save()


@bot.hybrid_command(name="time", description="Time remaining")
async def time(ctx):
    global start_time, total_time
    if start_time:
        elapsed = datetime.datetime.now() - start_time
        remaining = total_time - elapsed.seconds
        await ctx.send(f"Time remaining: {remaining} seconds.")
    else:
        await ctx.send("No question is currently active.")


@bot.hybrid_command(name="prelims",  description="Prelims format")
async def prelims(ctx):
    global current_question, current_team, answered, current_mode, start_time, total_time
    with open("prelims.json") as f:
        questions = json.load(f)
    answered = {}
    current_mode = "prelims"
    # stop trying to get questions if all the prelims questions are asked:
    if len(asked) == len(questions):
        embed = discord.Embed(
            title="All Questions have been asked", description="You have 2 minutes to answer all the questions.\n\nType all the answers in /prelim_answer.", color=discord.Color.red())
        await ctx.send(embed=embed)
        total_time = 40
        await asyncio.sleep(total_time)
        timeup = discord.Embed(
            title="Time's Up!", description="Time's up! The answers are being checked.", color=discord.Color.red()
        )
        await handle_prelims(ctx)
        await ctx.send(embed=timeup)
        return
    question = random.choice(questions)
    while question["mode"] != "prelims" or question["id"] in asked:
        question = random.choice(questions)
    current_question = question
    asked.append(question["id"])
    prelims_answers.append(question["answer"])
    current_question["channel_id"] = ctx.channel.id
    question_text = current_question["question"]
    if current_question["type"] == "guess" or current_question["type"] == "multi":
        embed = discord.Embed(
            title="Question", description=question_text, color=discord.Color.greyple())
        await ctx.send(embed=embed)
        await save()


async def mute_current_team(ctx):
    current_team_name = team_order[current_team]
    current_team_members = teams[current_team_name]["members"]
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    for member in current_team_members:
        await member.add_roles(role)
    await ctx.send(f"Team {current_team_name} has been muted for 1 minute.")
    await unmute_current_team(ctx)


async def unmute_current_team(ctx):
    await asyncio.sleep(60)
    current_team_name = team_order[current_team]
    current_team_members = teams[current_team_name]["members"]
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    for member in current_team_members:
        await member.remove_roles(role)
    await ctx.channel.send(f"Team {current_team_name} has been unmuted.")


async def start_timers(ctx, team, view):
    await ctx.channel.send("You have 30 seconds to answer the question.")
    await asyncio.sleep(30)
    global current_team, current_question
    if current_team == team and current_question != None:
        await bounce_questions(ctx, view)


async def bounce_questions(ctx, view):
    global current_team, attempted, current_question, current_mode, pounced
    current_team_name = team_order[current_team]
    if current_team_name not in attempted:
        attempted.append(current_team_name)
    if len(attempted) == len(team_order):

        current_team = (current_team + 1) % len(team_order)
        embed = discord.Embed(
            title="Question Closed", description="All teams have attempted the question. It is now closed.", color=discord.Color.blurple())
        teamlist = " ".join(correct_teams)
        if correct_teams == []:
            embed.add_field(
                name="No teams got the right answer.", value="Better luck next time!")
        else:
            embed.add_field(
                name=f"Teams who guessed right:", value=teamlist)
        embed.add_field(name="The Correct answer",
                        value=current_question["answer"])
        current_question = None
        current_mode = None
        attempted = []
        await save()
        await ctx.channel.send(embed=embed)
        return
    current_team = (current_team + 1) % len(team_order)
    while team_order[current_team] in pounced:
        current_team = (current_team + 1) % len(team_order)
    crt = discord.Embed(title="Question Bounced", description=f'''Current team: **Team {
                        team_order[current_team]}**''', color=discord.Color.green())
    for child in view.children:
        if child.label == "Pounce":
            view.remove_item(child)
    await save()
    await ctx.channel.send(embed=crt, view=view)
    await start_timers(ctx, current_team, view)


async def handle_guess_answer(message):
    global current_question
    guess = message.content.lower()
    correct = current_question["answer"]
    dist = distance(guess, correct.lower())
    if dist/(len(correct)) <= 0.2:
        await message.reply(embed=correct_embed)
        embed = discord.Embed(title="Correct Answer", description=f"{
                              message.author} got the correct answer!", color=discord.Color.green())
        embed.add_field(name="Correct Answer:", value=correct)
        await save()
        await message.channel.send(embed=embed)
        current_question = None


async def handle_multiple_answer(message):
    global current_question, answered_right
    answered[message.author.id] = True
    for word in [message.content.strip()]:
        for num, answer in enumerate(current_question['answer']):
            if answer not in answered_right:
                correct = answer
                dist = distance(word.lower(), correct.lower())
                if dist/(len(correct)) <= 0.2:
                    await message.reply(embed=correct_embed)
                    embed = discord.Embed(title="Correct Answer", description=f"{message.author.mention} got part {
                                          num+1} of the question right!", color=discord.Color.green())
                    embed.add_field(name="Answer:", value=correct)
                    answered_right.append(correct)
                    await message.channel.send(embed=embed)
                    if len(answered_right) == len(current_question['answer']):
                        answered_right = []
                        embed = discord.Embed(
                            title="Question Complete", description=f"The question has been answered!", color=discord.Color.green())
                        await message.channel.send(embed=embed)
                        current_question = None
                    return


async def handle_bounce_pounce(message):
    global current_question, current_team, current_mode, correct_teams, wrong_teams, answered
    guess = message.content.lower()
    correct = current_question["answer"]
    teamname = team_order[current_team]
    dist = distance(guess, correct.lower())
    if dist/(len(correct)) <= 0.2:
        if message.author in teams[teamname]["members"]:
            if correct_teams != []:
                teamlist = ", ".join(correct_teams)
                embed = discord.Embed(title="Correct Answer", description=f'''**Team {
                                      teamname}** got the correct answer!\n\n**Other teams that got the right answer**: {teamlist}\n\n**Correct Answer**: {current_question["answer"]}''', color=discord.Color.green())
            else:
                embed = discord.Embed(title="Correct Answer", description=f'''**Team {
                                      teamname}** was the only team to get the correct answer!\n\n**Correct Answer**: {current_question["answer"]}''', color=discord.Color.green())
            await message.channel.send(embed=embed)
            current_question = None
            current_mode = None
            current_team = (current_team + 1) % len(team_order)
            for team in correct_teams:
                await update_team_score(team, correct=True)
            for team in wrong_teams:
                await update_team_score(team, correct=False)
            correct_teams = []
            wrong_teams = []
            answered = {}


async def handle_prelims(ctx):
    global current_question, current_team, answered, current_mode, start_time, total_time, asked, team_answers
    with open("prelims.json") as f:
        questions = json.load(f)
    # search for channel named quiz-log:
    channel = discord.utils.get(ctx.guild.text_channels, name="quiz-log")
    for team in team_answers:
        embed = discord.Embed(
            title=f"Team {team} Answers", description="The answers submitted by the team are:", color=discord.Color(0x00ffff)
        )
        await channel.send(embed=embed)
        for i in range(len(questions)):
            qid = asked[i]
            for question in questions:
                if question["id"] == qid:
                    if team_answers[team][i] != None:
                        guess = team_answers[team][i].lower()
                        correct = question["answer"]
                        dist = distance(guess, correct.lower())
                        if dist/(len(correct)) <= 0.2:
                            teams[team]["score"] += 2
                            embed = discord.Embed(
                                title="Correct Answer", description=f"Team {team} got the correct answer for the question:\n\n**{question["question"]}**\n\n```Expected answer:```**```{question["answer"]}```**\n```Team's answer:```**```{team_answers[team][i]}```**", color=discord.Color.green()
                            )
                            await channel.send(embed=embed)
                        else:
                            embed = discord.Embed(
                                title="Wrong Answer", description=f"Team {team} got the wrong answer for the question:\n\n**{question["question"]}**\n\n```Expected answer:```**```{question["answer"]}```**\n```Team's answer:```**```{team_answers[team][i]}```**", color=discord.Color.red()
                            )
                            await channel.send(embed=embed)


# command to  answer prelim questions. 20 optional fields, one for each question


@bot.hybrid_command(name="prelim_answer", description="Submit your Answer to the question")
@app_commands.describe(ans1="Answer to the question 1", ans2="Answer to the question 2", ans3="Answer to the question 3", ans4="Answer to the question 4", ans5="Answer to the question 5", ans6="Answer to the question 6", ans7="Answer to the question 7", ans8="Answer to the question 8", ans9="Answer to the question 9", ans10="Answer to the question 10", ans11="Answer to the question 11", ans12="Answer to the question 12", ans13="Answer to the question 13", ans14="Answer to the question 14", ans15="Answer to the question 15", ans16="Answer to the question 16", ans17="Answer to the question 17", ans18="Answer to the question 18", ans19="Answer to the question 19", ans20="Answer to the question 20")
async def prelim_answer(ctx, ans1: str = None, ans2: str = None, ans3: str = None, ans4: str = None, ans5: str = None, ans6: str = None, ans7: str = None, ans8: str = None, ans9: str = None, ans10: str = None, ans11: str = None, ans12: str = None, ans13: str = None, ans14: str = None, ans15: str = None, ans16: str = None, ans17: str = None, ans18: str = None, ans19: str = None, ans20: str = None):
    global current_question, current_team, answered, current_mode, start_time, total_time, asked, team_answers
    uid = ctx.author.id
    cid = ctx.channel.id
    cteam = None
    for team in teams:
        if uid in teams[team]["members"]:
            cteam = team
            if cteam not in team_answers:
                team_answers[cteam] = {}
                for j in range(len(asked)):
                    team_answers[cteam][j] = None
                embed = discord.Embed(
                    title="Answers Submitted", description="Your answers have been submitted.", color=discord.Color.green()
                )
                await ctx.send(embed=embed, ephemeral=True)
                break
            else:
                embed = discord.Embed(
                    title="Answers Updated", description="Your answers have been updated.", color=discord.Color.green()
                )
                await ctx.send(embed=embed, ephemeral=True)
    answers = [ans1, ans2, ans3, ans4, ans5, ans6, ans7, ans8, ans9, ans10,
               ans11, ans12, ans13, ans14, ans15, ans15, ans16, ans17, ans18, ans19, ans20]
    for i in range(len(asked)):
        if team_answers[cteam] is {}:
            for j in range(len(asked)):
                team_answers[cteam][j] = None
        elif answers[i] != None:
            team_answers[cteam][i] = answers[i]
    await save()


@bot.hybrid_command(name="score", description="Get the score of a team.")
@app_commands.describe(team_name="Name of the team")
async def get_score(ctx, team_name: str):
    if team_name in teams:
        await ctx.send(f"Team {team_name} has {teams[team_name]['score']} points.")
    else:
        await ctx.send("Team does not exist.")


@bot.hybrid_command(name="team", description="Register a new team.")
@app_commands.describe(team_name="Name of the team")
async def register_team(ctx, team_name: str):
    global teams, team_order
    if team_name in teams:
        await ctx.send("Team already exists.")
    else:
        # Create a new role with a random color
        guild = ctx.guild
        user = ctx.author
        role_color = discord.Color(random.randint(0x000000, 0xFFFFFF))
        new_role = await guild.create_role(name=f"Team {team_name}", color=role_color)
        # generate a channel for the team:
        category = discord.utils.get(
            ctx.guild.categories, name="Team Channels")
        if category is None:
            category = await ctx.guild.create_category("Team Channels")
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            new_role: discord.PermissionOverwrite(read_messages=True)
        }
        underscored_name = "-".join(team_name.split())
        channel = await ctx.guild.create_text_channel(f"team-{underscored_name}", overwrites=overwrites, category=category)
        await channel.send(f"New Channel has been made for {team_name}.")
        # voice channel also:
        category = discord.utils.get(
            ctx.guild.categories, name="Team Voice Channels")
        if category is None:
            category = await ctx.guild.create_category("Team Voice Channels")
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(connect=False),
            new_role: discord.PermissionOverwrite(connect=True)
        }
        await ctx.guild.create_voice_channel(f"team-{underscored_name}", overwrites=overwrites, category=category)
        # Add the new team to the teams dictionary
        teams[team_name] = {"score": 0, "members": [], "role": new_role.id}
        team_order.append(team_name)

        await ctx.send(f"Team {team_name} registered successfully with role {new_role.mention}.")


@bot.hybrid_command(name="join", description="Join an existing team.")
@app_commands.describe(team_name="Name of the team to join")
async def join_team(ctx, team_name: str):
    if team_name not in teams:
        await ctx.send("Team does not exist.")
    else:
        teams[team_name]["members"].append(ctx.author.id)
        role = discord.utils.get(ctx.guild.roles, id=teams[team_name]["role"])
        await ctx.author.add_roles(role)

        await ctx.send(f"{ctx.author.mention} joined Team {team_name}.")


@bot.hybrid_command(name="leave", description="Leave your team.")
async def leave_team(ctx):
    global teams
    user = ctx.author
    for team, details in teams.items():
        if user.id in details["members"]:
            details["members"].remove(ctx.author.id)
            await ctx.send(f"{ctx.author.mention} left Team {team}.")
            role = discord.utils.get(
                ctx.guild.roles, id=teams[team]["role"])
            await user.remove_roles(role)
            return
    await ctx.send("You are not part of any team.")

# remove team


@bot.hybrid_command(name="remove_team", description="Remove a team.")
@app_commands.describe(team_name="Name of the team to remove")
async def remove_team(ctx, team_name: str):
    if team_name not in teams:
        await ctx.send("Team does not exist.")
    else:
        team = teams[team_name]
        role = discord.utils.get(ctx.guild.roles, id=team["role"])
        await role.delete()
        # remove team channel:
        for channel in ctx.guild.text_channels:
            underscored_name = "-".join(team_name.split())
            if channel.name == f"team-{underscored_name}":
                await channel.delete()
        for channel in ctx.guild.voice_channels:
            underscored_name = "-".join(team_name.split())
            if channel.name == f"team-{underscored_name}":
                await channel.delete()
        del teams[team_name]
        await ctx.send(f"Team {team_name} has been removed.")


async def update_team_score(user_id, channel_id, correct: bool):
    team_name = None
    for team, details in teams.items():
        if user_id in details["members"]:
            team_name = team
            break
    if team_name:
        if correct:
            teams[team_name]["score"] += CORRECT_ANSWER_POINTS
        else:
            teams[team_name]["score"] += WRONG_ANSWER_PENALTY
        embed = discord.Embed(
            title="Score Update", description=f"Team {team_name} now has {teams[team_name]['score']} points.", color=discord.Color(0x00ff00)
        )
        await bot.get_channel(channel_id).send(embed=embed)


@bot.hybrid_command(name="answer", description="Submit your Answer to the question")
@app_commands.describe(ans="Answer to the question")
async def submit_answer(ctx, ans: str):
    global current_question, current_mode, current_team, correct_teams, wrong_teams, rem_time, answered
    if current_mode == "bounce_pounce":
        user = ctx.author.id
        flag = 0
        for team, timestamp in pounced:
            if team not in answered:
                if user in teams[team]["members"]:
                    flag = 1
                    curr_time = datetime.datetime.now()
                    if (curr_time - timestamp).seconds > rem_time:
                        await ctx.send("You have exceeded the time limit to answer the question.", ephemeral=True)
                        return
                    guess = ans.lower()
                    correct = current_question["answer"]
                    dist = distance(guess, correct.lower())
                    if dist/(len(correct)) <= 0.2:
                        correct_teams.append(team)
                    else:
                        wrong_teams.append(team)
                    answered[team] = True
        if flag == 0:
            await ctx.send("You have not pounced on the question!", ephemeral=True)
            return
        await ctx.send("Your answer has been submitted.", ephemeral=True)

    else:
        if current_question["type"] == "guess":
            guess = ans.lower()
            correct = current_question["answer"]
            dist = distance(guess, correct.lower())
            if dist/(len(correct)) <= 0.2:
                embed = correct_embed
                embed.add_field(name=f"{ctx.author}'s Answer:", value=ans)
                await ctx.send(embed=embed)
                current_question = None
            else:
                embed = wrong_embed
                embed.add_field(name=f"{ctx.author}'s Answer:", value=ans)
                await ctx.send(embed=embed)
            embed = None
        else:
            await ctx.send("This command is only for Guess type questions.")


@bot.hybrid_command(name="new", description="Add a new question to the set.")
@app_commands.describe(ques_type="Type of question", question="The question text", options="Options for MCQ (comma separated)", answer="The correct answer")
async def add_question(ctx, ques_type: str, question: str, options: str = None, answer: str = None):
    global questions
    new_question = {
        "type": ques_type,
        "question": question,
        "answer": answer
    }
    if ques_type == "mcq":
        new_question["options"] = options.split(',')

    questions.append(new_question)
    with open('questions.json', 'w') as f:
        json.dump(questions, f, indent=4)

    await ctx.send("New question added successfully.")


@bot.hybrid_command(name="ask", description="Ask a question directly without adding to the set.")
@app_commands.describe(ques_type="Type of question", question="The question text", mode="Bounce amd pounce(Optional)",  image_url="URL of the image", options="Options for MCQ (comma separated)", answers="The correct answer")
async def ask_direct_question(ctx, ques_type: str, question: str, mode: str = None, image_url: str = None, options: str = None, answers: str = None):
    global current_question, current_mode, current_team, start_time
    current_mode = mode
    if ques_type == "mcq":
        current_question = {
            "type": ques_type,
            "question": question,
            "answer": answers,
            "channel_id": ctx.channel.id
        }
        current_question["options"] = options.split(',')
        global answered
        answered = {}
        view = QuestionView(current_question)
        embed = discord.Embed(
            title="Question", description=question, color=discord.Colour(0x1d1e21))
        if image_url:
            embed.set_image(url=image_url)
        for ans in current_question["options"]:
            btn = Button(
                label=ans, style=discord.ButtonStyle.primary, custom_id=ans)
            btn.callback = view.answer_check
            view.add_item(btn)
        await ctx.send("Sending the question...", ephemeral=True, delete_after=3)
        message = await ctx.channel.send(embed=embed, view=view)
        view.message = message
    elif ques_type == "guess":
        current_question = {
            "type": ques_type,
            "question": question,
            "answer": answers,
            "channel_id": ctx.channel.id
        }
        embed = discord.Embed(
            title="Question", description=question, color=discord.Colour(0x1d1e21))
        if image_url:
            embed.set_image(url=image_url)

        await ctx.send("Sending the question...", ephemeral=True, delete_after=3)
        await ctx.channel.send(embed=embed)
        if mode == "bounce_pounce":
            view = QuestionView(current_question, mode)
            crt = discord.Embed(title="Current Team", description=f"Team {
                                team_order[current_team]}", color=discord.Color.green())
            message = await ctx.send(embed=crt, view=view)
            start_time = datetime.datetime.now()
            view.message = message
            await mute_current_team(ctx)
            await start_timers(ctx, current_team, view)
    elif ques_type == "multi":
        current_question = {
            "type": ques_type,
            "question": question,
            "answer": [answer.strip() for answer in answers.split(',')],
            "channel_id": ctx.channel.id
        }
        embed = discord.Embed(
            title="Question", description=question, color=discord.Colour(0x1d1e21))
        if image_url:
            embed.set_image(url=image_url)
        await ctx.send("Sending the question...", ephemeral=True, delete_after=3)
        await ctx.channel.send(embed=embed)

client.run(os.getenv('TOKEN'))
