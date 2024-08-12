---

<h1 align="center">🎉 Welcome to QuizBot 🎉</h1>
<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-0.8-blue.svg?cacheSeconds=2592000" />
  <img alt="Made with Python" src="https://img.shields.io/badge/made%20with-python-blue.svg" />
</p>

> **QuizBot** is an interactive Discord bot that brings quiz competitions to life with ease. Using simple slash commands, QuizBot can host various quiz formats, track scores, and provide a fun, engaging experience for users. The bot reads questions from a JSON file, supports multiple question types, and keeps track of user and team scores in real-time.

## 🌟 Features

- **Interactive Quiz Hosting**: Conduct quizzes directly in Discord channels using slash commands.
- **Multiple Question Types**: Supports various question formats, including multiple-choice, guess-the-answer, and more.
- **Team Management**: Allows users to create, join, and manage teams for a competitive quiz experience.
- **Real-Time Scoring**: Tracks scores for individual users and teams, displaying leaderboards and progress updates.
- **Customizable Questions**: Load your own questions from JSON files or create new ones on the fly.
- **Save & Load Progress**: Automatically saves quiz progress and loads it when the bot restarts.

## 📚 Getting Started

### Prerequisites

- Python 3.8+
- Discord Account and Server
- A Discord Bot Token

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Hydraknight/QuizBot.git
   cd QuizBot
   ```

2. **Install the required Python packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your environment variables**:
   - Create a `.env` file in the root directory and add your Discord bot token:
     ```
     TOKEN=your-discord-bot-token
     ```

4. **Run the bot**:
   ```bash
   python bot.py
   ```

### Commands Overview

- **/question**: Start a quiz question.
- **/answer**: Submit an answer to the active question.
- **/score**: View the current score.
- **/reset**: Reset the quiz settings.
- **/team**: Register a new team.
- **/join**: Join an existing team.

For a full list of commands, refer to the [documentation](#).

## 🤖 Bot Architecture

QuizBot is built using the [discord.py](https://discordpy.readthedocs.io/) library. It leverages Discord's slash commands to create an intuitive and responsive user interface. The bot’s core features are structured into various commands and event listeners that handle user interactions, game logic, and scorekeeping.

### Key Components

- **Question Management**: Handles the display and timing of questions.
- **Scorekeeping**: Manages the scoring system for teams and individuals.
- **Team Management**: Facilitates the creation and management of teams.
- **Persistence**: Saves and loads the state of ongoing quizzes to ensure continuity.

## 👤 Author

**Hydraknight**

- GitHub: [@Hydraknight](https://github.com/Hydraknight)

## 🛠 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/Hydraknight/QuizBot/issues).

## 🙌 Show Your Support

Give a ⭐️ if you like this project!

---
