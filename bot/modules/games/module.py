"""Games module - Complete game suite with trivia, puzzles, and more."""

import random
import re
from typing import Dict, Optional
from aiogram.types import Message, Poll
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class GamesConfig(BaseModel):
    """Configuration for games module."""
    enabled: bool = True
    xp_rewards: int = 10
    coin_rewards: int = 5
    trivia_difficulty: str = "medium"
    max_questions: int = 10


class GamesModule(NexusModule):
    """Complete game suite with multiple games."""

    name = "games"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Complete game suite with trivia, puzzles, and more"
    category = ModuleCategory.GAMES

    config_schema = GamesConfig
    default_config = GamesConfig().dict()

    commands = [
        CommandDef(
            name="trivia",
            description="Start a trivia game",
            admin_only=False,
            args="[category] [difficulty] [questions]",
        ),
        CommandDef(
            name="quiz",
            description="Start a quick quiz",
            admin_only=False,
            args="[question] [options...]",
        ),
        CommandDef(
            name="wordle",
            description="Play Wordle game",
            admin_only=False,
        ),
        CommandDef(
            name="hangman",
            description="Play Hangman",
            admin_only=False,
        ),
        CommandDef(
            name="chess",
            description="Play Chess (start a game)",
            admin_only=False,
            args="[@opponent]",
        ),
        CommandDef(
            name="tictactoe",
            description="Play Tic Tac Toe",
            admin_only=False,
            args="[@opponent]",
        ),
        CommandDef(
            name="rps",
            description="Rock Paper Scissors",
            admin_only=False,
            args="[rock|paper|scissors]",
        ),
        CommandDef(
            name="8ball",
            description="Magic 8-Ball prediction",
            admin_only=False,
            args="<question>",
        ),
        CommandDef(
            name="dice",
            description="Roll dice",
            admin_only=False,
            args="[sides]",
        ),
        CommandDef(
            name="coinflip",
            description="Flip a coin",
            admin_only=False,
        ),
        CommandDef(
            name="wheel",
            description="Spin the wheel of fortune",
            admin_only=False,
        ),
        CommandDef(
            name="memory",
            description="Memory card game",
            admin_only=False,
        ),
        CommandDef(
            name="guessnumber",
            description="Guess the number game",
            admin_only=False,
            args="[min] [max]",
        ),
        CommandDef(
            name="unscramble",
            description="Unscramble the word",
            admin_only=False,
        ),
        CommandDef(
            name="connect4",
            description="Play Connect Four",
            admin_only=False,
            args="[@opponent]",
        ),
        CommandDef(
            name="battleship",
            description="Play Battleship",
            admin_only=False,
            args="[@opponent]",
        ),
        CommandDef(
            name="minesweeper",
            description="Play Minesweeper",
            admin_only=False,
            args="[difficulty]",
        ),
        CommandDef(
            name="sudoku",
            description="Play Sudoku",
            admin_only=False,
            args="[difficulty]",
        ),
        CommandDef(
            name="mastermind",
            description="Play Mastermind code-breaking",
            admin_only=False,
        ),
        CommandDef(
            name="riddle",
            description="Get a riddle to solve",
            admin_only=False,
        ),
    ]

    # Trivia questions database
    TRIVIA_QUESTIONS = {
        "science": [
            {"q": "What is the chemical symbol for Gold?", "a": ["Au"], "options": ["Au", "Ag", "Fe", "Cu"]},
            {"q": "What planet is known as the Red Planet?", "a": ["Mars"], "options": ["Mars", "Venus", "Jupiter", "Saturn"]},
            {"q": "What is the hardest natural substance on Earth?", "a": ["Diamond"], "options": ["Diamond", "Steel", "Titanium", "Iron"]},
            {"q": "How many bones are in the adult human body?", "a": ["206"], "options": ["206", "208", "204", "210"]},
            {"q": "What gas do plants absorb from the atmosphere?", "a": ["Carbon dioxide", "CO2"], "options": ["Carbon dioxide", "Oxygen", "Nitrogen", "Hydrogen"]},
        ],
        "history": [
            {"q": "In which year did World War II end?", "a": ["1945"], "options": ["1945", "1944", "1946", "1943"]},
            {"q": "Who was the first President of the United States?", "a": ["George Washington"], "options": ["George Washington", "John Adams", "Thomas Jefferson", "Benjamin Franklin"]},
            {"q": "Which ancient wonder was located in Egypt?", "a": ["Great Pyramid of Giza"], "options": ["Great Pyramid of Giza", "Hanging Gardens", "Colossus", "Lighthouse"]},
            {"q": "What year did the Titanic sink?", "a": ["1912"], "options": ["1912", "1913", "1911", "1910"]},
            {"q": "Who painted the Mona Lisa?", "a": ["Leonardo da Vinci"], "options": ["Leonardo da Vinci", "Michelangelo", "Raphael", "Donatello"]},
        ],
        "geography": [
            {"q": "What is the largest country by area?", "a": ["Russia"], "options": ["Russia", "Canada", "China", "USA"]},
            {"q": "What is the longest river in the world?", "a": ["Nile", "River Nile"], "options": ["Nile", "Amazon", "Yangtze", "Mississippi"]},
            {"q": "Which continent has the most countries?", "a": ["Africa"], "options": ["Africa", "Asia", "Europe", "South America"]},
            {"q": "What is the capital of Japan?", "a": ["Tokyo"], "options": ["Tokyo", "Kyoto", "Osaka", "Nagoya"]},
            {"q": "Which country has the most islands?", "a": ["Sweden"], "options": ["Sweden", "Norway", "Finland", "Indonesia"]},
        ],
        "entertainment": [
            {"q": "Who directed the movie 'Inception'?", "a": ["Christopher Nolan"], "options": ["Christopher Nolan", "Steven Spielberg", "James Cameron", "Quentin Tarantino"]},
            {"q": "What is the highest-grossing film of all time?", "a": ["Avatar"], "options": ["Avatar", "Avengers: Endgame", "Titanic", "Star Wars"]},
            {"q": "Who wrote 'Harry Potter'?", "a": ["J.K. Rowling"], "options": ["J.K. Rowling", "Stephen King", "George R.R. Martin", "J.R.R. Tolkien"]},
            {"q": "What year was the first iPhone released?", "a": ["2007"], "options": ["2007", "2008", "2006", "2009"]},
            {"q": "Who is known as the 'King of Pop'?", "a": ["Michael Jackson"], "options": ["Michael Jackson", "Elvis Presley", "Prince", "Madonna"]},
        ],
        "sports": [
            {"q": "How many players are on a soccer team?", "a": ["11"], "options": ["11", "10", "9", "12"]},
            {"q": "In which sport would you perform a slam dunk?", "a": ["Basketball"], "options": ["Basketball", "Volleyball", "Tennis", "Baseball"]},
            {"q": "How often is the FIFA World Cup held?", "a": ["4 years"], "options": ["4 years", "2 years", "Every year", "3 years"]},
            {"q": "What country won the first FIFA World Cup?", "a": ["Uruguay"], "options": ["Uruguay", "Brazil", "Argentina", "Italy"]},
            {"q": "In tennis, what does 'love' mean?", "a": ["Zero", "0"], "options": ["Zero", "One", "Two", "Three"]},
        ],
    }

    # Riddles database
    RIDDLES = [
        {"q": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "a": ["echo", "an echo"]},
        {"q": "The more you take, the more you leave behind. What am I?", "a": ["footsteps", "footsteps"]},
        {"q": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?", "a": ["map", "a map"]},
        {"q": "What has keys but can't open locks?", "a": ["piano", "a piano", "keyboard", "a keyboard"]},
        {"q": "What can travel around the world while staying in a corner?", "a": ["stamp", "a stamp"]},
        {"q": "What gets wet while drying?", "a": ["towel", "a towel"]},
        {"q": "What has a neck but no head?", "a": ["bottle", "a bottle"]},
        {"q": "What goes up but never comes down?", "a": ["age", "your age"]},
    ]

    # 8-Ball responses
    MAGIC_8_BALL = [
        "It is certain", "It is decidedly so", "Without a doubt", "Yes definitely",
        "You may rely on it", "As I see it, yes", "Most likely", "Outlook good",
        "Yes", "Signs point to yes", "Reply hazy, try again", "Ask again later",
        "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
        "Don't count on it", "My reply is no", "My sources say no",
        "Outlook not so good", "Very doubtful"
    ]

    # Words for word games
    WORDS = [
        "apple", "beach", "cloud", "dance", "eagle", "flame", "grape", "house",
        "image", "juice", "knife", "lemon", "music", "night", "ocean", "party",
        "quiet", "radio", "snake", "tiger", "unity", "video", "water", "xenon",
        "young", "zebra", "brave", "crisp", "dream", "float", "gloss", "happy"
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("trivia", self.cmd_trivia)
        self.register_command("quiz", self.cmd_quiz)
        self.register_command("wordle", self.cmd_wordle)
        self.register_command("hangman", self.cmd_hangman)
        self.register_command("chess", self.cmd_chess)
        self.register_command("tictactoe", self.cmd_tictactoe)
        self.register_command("rps", self.cmd_rps)
        self.register_command("8ball", self.cmd_8ball)
        self.register_command("dice", self.cmd_dice)
        self.register_command("coinflip", self.cmd_coinflip)
        self.register_command("wheel", self.cmd_wheel)
        self.register_command("memory", self.cmd_memory)
        self.register_command("guessnumber", self.cmd_guessnumber)
        self.register_command("unscramble", self.cmd_unscramble)
        self.register_command("connect4", self.cmd_connect4)
        self.register_command("battleship", self.cmd_battleship)
        self.register_command("minesweeper", self.cmd_minesweeper)
        self.register_command("sudoku", self.cmd_sudoku)
        self.register_command("mastermind", self.cmd_mastermind)
        self.register_command("riddle", self.cmd_riddle)

    async def cmd_trivia(self, ctx: NexusContext):
        """Start trivia game."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        # Parse arguments
        category = None
        difficulty = ctx.group.module_configs.get("games", {}).get("trivia_difficulty", "medium")
        num_questions = 5

        if args:
            if args[0].lower() in self.TRIVIA_QUESTIONS:
                category = args[0].lower()
                if len(args) > 1 and args[1].lower() in ["easy", "medium", "hard"]:
                    difficulty = args[1].lower()
                if len(args) > 2 and args[2].isdigit():
                    num_questions = min(int(args[2]), 10)
            elif args[0].isdigit():
                num_questions = min(int(args[0]), 10)

        # Get questions
        all_questions = []
        if category:
            questions = self.TRIVIA_QUESTIONS.get(category, [])
        else:
            questions = []
            for cat_questions in self.TRIVIA_QUESTIONS.values():
                questions.extend(cat_questions)

        random.shuffle(questions)
        questions = questions[:num_questions]

        if not questions:
            await ctx.reply("❌ No questions available for this category")
            return

        # Start first question
        self._current_trivia[ctx.chat_id] = {
            "questions": questions,
            "current": 0,
            "score": 0,
            "category": category,
            "difficulty": difficulty
        }

        await self._send_trivia_question(ctx)

    async def _send_trivia_question(self, ctx: NexusContext):
        """Send next trivia question."""
        game = self._current_trivia.get(ctx.chat_id)
        if not game:
            return

        if game["current"] >= len(game["questions"]):
            # Game over
            await ctx.reply(
                f"🎉 **Trivia Complete!**\n\n"
                f"Score: {game['score']}/{len(game['questions'])}\n"
                f"Category: {game['category'] or 'Mixed'}\n"
                f"Difficulty: {game['difficulty']}\n\n"
                f"🏆 {ctx.user.first_name} wins {game['score'] * 10} XP and {game['score'] * 5} coins!"
            )
            del self._current_trivia[ctx.chat_id]
            return

        question = game["questions"][game["current"]]
        game["current"] += 1

        # Send as poll
        poll = Poll(
            id=f"trivia_{ctx.chat_id}",
            question=f"❓ Q{game['current']}/{len(game['questions'])}: {question['q']}",
            options=question["options"],
            type="quiz",
            correct_option_id=question["options"].index(question["a"][0]),
            is_anonymous=False,
            is_closed=False
        )

        await ctx.reply(
            f"❓ **Question {game['current']}/{len(game['questions'])}**\n\n"
            f"{question['q']}\n\n"
            f"📊 Score: {game['score']}",
            buttons=[[{"text": f"Next Question", "callback_data": f"trivia_next_{ctx.chat_id}"}]]
        )

    async def cmd_quiz(self, ctx: NexusContext):
        """Create a quick quiz."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 3:
            await ctx.reply(
                "❌ Usage: `/quiz <question> <correct_answer> <wrong_answer1> [wrong_answer2]...`\n\n"
                "Example: `/quiz What is 2+2? 4 3 5 6`"
            )
            return

        question = args[0]
        correct = args[1]
        wrong = args[2:]

        options = [correct] + wrong
        random.shuffle(options)

        poll = Poll(
            id=f"quiz_{ctx.message.message_id}",
            question=question,
            options=options,
            type="quiz",
            correct_option_id=options.index(correct),
            is_anonymous=False,
            is_closed=False
        )

        await ctx.bot.send_poll(
            chat_id=ctx.chat_id,
            question=poll.question,
            options=poll.options,
            type=poll.type,
            correct_option_id=poll.correct_option_id,
            is_anonymous=poll.is_anonymous
        )

    async def cmd_wordle(self, ctx: NexusContext):
        """Play Wordle."""
        word = random.choice(self.WORDS).upper()

        self._wordle_games[ctx.chat_id] = {
            "word": word,
            "attempts": 0,
            "max_attempts": 6
        }

        await ctx.reply(
            f"🎮 **Wordle**\n\n"
            f"Guess the 5-letter word!\n"
            f"You have 6 attempts.\n\n"
            f"🟢 = Correct letter, correct position\n"
            f"🟡 = Correct letter, wrong position\n"
            f"⚪ = Wrong letter\n\n"
            f"Send your guess as a message!",
            buttons=[[{"text": "Give Up", "callback_data": f"wordle_giveup_{ctx.chat_id}"}]]
        )

    async def cmd_hangman(self, ctx: NexusContext):
        """Play Hangman."""
        word = random.choice(self.WORDS).upper()
        masked = "_" * len(word)

        self._hangman_games[ctx.chat_id] = {
            "word": word,
            "masked": masked,
            "wrong": 0,
            "max_wrong": 6,
            "guessed": []
        }

        await ctx.reply(
            f"🎮 **Hangman**\n\n"
            f"Word: `{masked}`\n"
            f"Wrong guesses: 0/6\n\n"
            f"Guess a letter by typing it!",
            buttons=[[{"text": "Give Up", "callback_data": f"hangman_giveup_{ctx.chat_id}"}]]
        )

    async def cmd_chess(self, ctx: NexusContext):
        """Start Chess game."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        opponent = None
        if args and ctx.message.reply_to_message and ctx.message.reply_to_message.from_user:
            opponent = ctx.message.reply_to_message.from_user.mention

        if not opponent:
            opponent = args[0] if args else "Anyone"

        await ctx.reply(
            f"♟️ **Chess Challenge!**\n\n"
            f"👤 {ctx.user.mention} vs {opponent}\n\n"
            f"🎮 Use the button below to play in the browser:\n\n"
            f"[🎯 Play Chess](https://www.chess.com/play/computer)",
            buttons=[[
                {"text": "🎮 Play Online", "url": "https://www.chess.com/play/computer"}
            ]]
        )

    async def cmd_tictactoe(self, ctx: NexusContext):
        """Play Tic Tac Toe."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        opponent = None
        if ctx.message.reply_to_message and ctx.message.reply_to_message.from_user:
            opponent = ctx.message.reply_to_message.from_user.mention
        elif args:
            opponent = args[0]

        if not opponent:
            opponent = "Anyone"

        board = [
            ["⬜", "⬜", "⬜"],
            ["⬜", "⬜", "⬜"],
            ["⬜", "⬜", "⬜"]
        ]

        self._tictactoe_games[ctx.chat_id] = {
            "board": board,
            "current": "❌",
            "players": [ctx.user.mention, opponent],
            "turn": 0
        }

        board_text = self._format_tictactoe_board(board)

        await ctx.reply(
            f"❌⭕ **Tic Tac Toe**\n\n"
            f"{ctx.user.mention} (❌) vs {opponent} (⭕)\n\n"
            f"{board_text}\n\n"
            f"📍 Use coordinates (1-9) to play:",
            buttons=[
                [{"text": "1", "callback_data": f"ttt_{ctx.chat_id}_0"}, {"text": "2", "callback_data": f"ttt_{ctx.chat_id}_1"}, {"text": "3", "callback_data": f"ttt_{ctx.chat_id}_2"}],
                [{"text": "4", "callback_data": f"ttt_{ctx.chat_id}_3"}, {"text": "5", "callback_data": f"ttt_{ctx.chat_id}_4"}, {"text": "6", "callback_data": f"ttt_{ctx.chat_id}_5"}],
                [{"text": "7", "callback_data": f"ttt_{ctx.chat_id}_6"}, {"text": "8", "callback_data": f"ttt_{ctx.chat_id}_7"}, {"text": "9", "callback_data": f"ttt_{ctx.chat_id}_8"}]
            ]
        )

    def _format_tictactoe_board(self, board):
        """Format Tic Tac Toe board."""
        rows = []
        for row in board:
            rows.append("".join(row))
        return "\n".join(rows)

    async def cmd_rps(self, ctx: NexusContext):
        """Rock Paper Scissors."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        choices = ["🪨 Rock", "📄 Paper", "✂️ Scissors"]
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

        if not args or args[0].lower() not in ["rock", "paper", "scissors"]:
            await ctx.reply(
                "❌ Usage: `/rps <rock|paper|scissors>`\n\n"
                f"Examples:\n"
                f"• `/rps rock`\n"
                f"• `/rps paper`\n"
                f"• `/rps scissors`"
            )
            return

        user_choice = args[0].lower()
        bot_choice = random.choice(["rock", "paper", "scissors"])

        user_emoji = emojis[user_choice]
        bot_emoji = emojis[bot_choice]

        # Determine winner
        if user_choice == bot_choice:
            result = "🤝 It's a tie!"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "🎉 You win!"
            await ctx.award_xp(ctx.user.user_id, 5, "rps win")
        else:
            result = "🤖 Bot wins!"

        await ctx.reply(
            f"🪨📄✂️ **Rock Paper Scissors**\n\n"
            f"{ctx.user.mention}: {user_emoji}\n"
            f"Bot: {bot_emoji}\n\n"
            f"**{result}**"
        )

    async def cmd_8ball(self, ctx: NexusContext):
        """Magic 8-Ball."""
        args = " ".join(ctx.message.text.split()[1:]) if ctx.message.text else ""

        if not args:
            await ctx.reply("❌ Usage: `/8ball <question>`")
            return

        response = random.choice(self.MAGIC_8_BALL)

        await ctx.reply(
            f"🎱 **Magic 8-Ball**\n\n"
            f"❓ Question: {args}\n\n"
            f"🔮 Answer: {response}"
        )

    async def cmd_dice(self, ctx: NexusContext):
        """Roll dice."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        sides = 6
        if args and args[0].isdigit() and int(args[0]) > 0:
            sides = min(int(args[0]), 100)

        result = random.randint(1, sides)

        dice_emojis = {
            1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"
        }

        emoji = dice_emojis.get(result, "🎲")

        await ctx.reply(
            f"🎲 **Dice Roll**\n\n"
            f"{emoji} You rolled: **{result}**\n"
            f"(1-{sides} sided die)"
        )

    async def cmd_coinflip(self, ctx: NexusContext):
        """Flip a coin."""
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙"

        await ctx.reply(
            f"{emoji} **Coin Flip**\n\n"
            f"Result: **{result}**"
        )

    async def cmd_wheel(self, ctx: NexusContext):
        """Spin the wheel of fortune."""
        prizes = [
            "🎁 100 coins", "🌟 50 XP", "🎫 Nothing", "💎 Rare Item",
            "⭐ 25 XP", "🍀 Lucky bonus", "🎊 Jackpot 500 coins", "🎫 Nothing",
            "💰 200 coins", "🏆 Badge", "🎫 Nothing", "🎁 50 coins"
        ]

        weights = [15, 20, 30, 5, 20, 10, 2, 30, 10, 3, 30, 15]

        prize = random.choices(prizes, weights=weights)[0]

        if "coins" in prize:
            amount = int(prize.split()[1])
            # Add coins to user wallet (would use economy module)
        elif "XP" in prize:
            amount = int(prize.split()[1])
            await ctx.award_xp(ctx.user.user_id, amount, "wheel spin")

        await ctx.reply(
            f"🎡 **Wheel of Fortune**\n\n"
            f"🎯 Spinning...\n"
            f"🎉 You won: **{prize}**!"
        )

    async def cmd_memory(self, ctx: NexusContext):
        """Memory card game."""
        emojis = ["🍎", "🍊", "🍋", "🍇", "🍓", "🍒", "🥝", "🍑"]
        cards = emojis * 2
        random.shuffle(cards)

        self._memory_games[ctx.chat_id] = {
            "cards": cards,
            "flipped": [False] * 16,
            "matched": [False] * 16,
            "selected": None,
            "moves": 0
        }

        await ctx.reply(
            f"🧠 **Memory Game**\n\n"
            f"Find all matching pairs!\n\n"
            f"🃏 [1][2][3][4]\n"
            f"🃏 [5][6][7][8]\n"
            f"🃏 [9][10][11][12]\n"
            f"🃏 [13][14][15][16]\n\n"
            f"Type numbers 1-16 to flip cards!",
            buttons=[[{"text": "🔄 New Game", "callback_data": f"memory_new_{ctx.chat_id}"}]]
        )

    async def cmd_guessnumber(self, ctx: NexusContext):
        """Guess the number."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        min_num = 1
        max_num = 100

        if len(args) >= 2 and args[0].isdigit() and args[1].isdigit():
            min_num = int(args[0])
            max_num = int(args[1])

        number = random.randint(min_num, max_num)

        self._guessnumber_games[ctx.chat_id] = {
            "number": number,
            "attempts": 0,
            "min": min_num,
            "max": max_num
        }

        await ctx.reply(
            f"🔢 **Guess the Number**\n\n"
            f"I'm thinking of a number between {min_num} and {max_num}.\n\n"
            f"Type your guess!",
            buttons=[[{"text": "🎲 Random Guess", "callback_data": f"guess_random_{ctx.chat_id}"}]]
        )

    async def cmd_unscramble(self, ctx: NexusContext):
        """Unscramble the word."""
        word = random.choice(self.WORDS)
        scrambled = list(word)
        random.shuffle(scrambled)
        scrambled_word = "".join(scrambled).upper()

        self._unscramble_games[ctx.chat_id] = {
            "word": word,
            "scrambled": scrambled_word,
            "attempts": 0
        }

        await ctx.reply(
            f"🔤 **Unscramble**\n\n"
            f"Unscramble this word:\n\n"
            f"**{scrambled_word}**\n\n"
            f"Type your answer!",
            buttons=[[{"text": "💡 Hint", "callback_data": f"unscramble_hint_{ctx.chat_id}"}]]
        )

    async def cmd_connect4(self, ctx: NexusContext):
        """Play Connect Four."""
        opponent = "Anyone"
        if ctx.message.reply_to_message and ctx.message.reply_to_message.from_user:
            opponent = ctx.message.reply_to_message.from_user.mention

        board = [["⬜" for _ in range(7)] for _ in range(6)]

        self._connect4_games[ctx.chat_id] = {
            "board": board,
            "current": "🔴",
            "players": [ctx.user.mention, opponent],
            "turn": 0
        }

        board_text = self._format_connect4_board(board)

        await ctx.reply(
            f"🔴🟡 **Connect Four**\n\n"
            f"{ctx.user.mention} (🔴) vs {opponent} (🟡)\n\n"
            f"{board_text}\n\n"
            f"📍 Choose a column (1-7):",
            buttons=[
                [{"text": "1", "callback_data": f"c4_{ctx.chat_id}_0"}, {"text": "2", "callback_data": f"c4_{ctx.chat_id}_1"}, {"text": "3", "callback_data": f"c4_{ctx.chat_id}_2"}, {"text": "4", "callback_data": f"c4_{ctx.chat_id}_3"}],
                [{"text": "5", "callback_data": f"c4_{ctx.chat_id}_4"}, {"text": "6", "callback_data": f"c4_{ctx.chat_id}_5"}, {"text": "7", "callback_data": f"c4_{ctx.chat_id}_6"}]
            ]
        )

    def _format_connect4_board(self, board):
        """Format Connect Four board."""
        rows = []
        for row in board:
            rows.append("|".join(row))
        return "\n".join(rows)

    async def cmd_battleship(self, ctx: NexusContext):
        """Play Battleship."""
        opponent = "Anyone"
        if ctx.message.reply_to_message and ctx.message.reply_to_message.from_user:
            opponent = ctx.message.reply_to_message.from_user.mention

        self._battleship_games[ctx.chat_id] = {
            "player1": {"name": ctx.user.mention, "ships": [], "hits": []},
            "player2": {"name": opponent, "ships": [], "hits": []},
            "turn": 0
        }

        await ctx.reply(
            f"⚓ **Battleship**\n\n"
            f"{ctx.user.mention} vs {opponent}\n\n"
            f"🎮 Coordinate system: A-J (columns) x 1-10 (rows)\n\n"
            f"Place your ships: `/place <type> <coord> <orientation>`\n"
            f"Ship types: carrier(5), battleship(4), cruiser(3), submarine(3), destroyer(2)\n\n"
            f"Example: `/place carrier A1 horizontal`"
        )

    async def cmd_minesweeper(self, ctx: NexusContext):
        """Play Minesweeper."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        difficulty = (args[0].lower() if args else "medium")

        configs = {
            "easy": {"size": 8, "mines": 10},
            "medium": {"size": 10, "mines": 20},
            "hard": {"size": 12, "mines": 35}
        }

        config = configs.get(difficulty, configs["medium"])
        size = config["size"]
        mines = config["mines"]

        self._minesweeper_games[ctx.chat_id] = {
            "size": size,
            "mines": mines,
            "revealed": [[False for _ in range(size)] for _ in range(size)],
            "game_over": False
        }

        await ctx.reply(
            f"💣 **Minesweeper** ({difficulty})\n\n"
            f"Grid: {size}x{size}\n"
            f"Mines: {mines}\n\n"
            f"📍 Reveal a cell: `/reveal <row> <col>`\n"
            f"Example: `/reveal 3 4`"
        )

    async def cmd_sudoku(self, ctx: NexusContext):
        """Play Sudoku."""
        args = ctx.message.text.split()[1:] if ctx.message.text else []
        difficulty = (args[0].lower() if args else "medium")

        await ctx.reply(
            f"🧩 **Sudoku** ({difficulty})\n\n"
            f"🎮 Use the button below to play:\n\n"
            f"[🎯 Play Sudoku](https://www.sudoku.com/)",
            buttons=[[
                {"text": "🎮 Play Online", "url": "https://www.sudoku.com/"}
            ]]
        )

    async def cmd_mastermind(self, ctx: NexusContext):
        """Play Mastermind."""
        code = [random.randint(1, 6) for _ in range(4)]

        self._mastermind_games[ctx.chat_id] = {
            "code": code,
            "attempts": 0,
            "max_attempts": 10
        }

        await ctx.reply(
            f"🎯 **Mastermind**\n\n"
            f"Guess the 4-digit code!\n"
            f"Digits: 1-6\n"
            f"Attempts: 10\n\n"
            f"📊 After each guess, you'll get:\n"
            f"🔴 = Correct digit, correct position\n"
            f"🟡 = Correct digit, wrong position\n\n"
            f"Type your 4-digit guess!",
            buttons=[[{"text": "🎲 Random Guess", "callback_data": f"mm_random_{ctx.chat_id}"}]]
        )

    async def cmd_riddle(self, ctx: NexusContext):
        """Get a riddle."""
        riddle = random.choice(self.RIDDLES)

        self._riddles[ctx.chat_id] = {
            "question": riddle["q"],
            "answer": riddle["a"],
            "attempts": 0
        }

        await ctx.reply(
            f"🤔 **Riddle**\n\n"
            f"{riddle['q']}\n\n"
            f"💡 Type your answer!",
            buttons=[[{"text": "💡 Give Up", "callback_data": f"riddle_giveup_{ctx.chat_id}"}]]
        )

    # Game state dictionaries
    _current_trivia = {}
    _wordle_games = {}
    _hangman_games = {}
    _tictactoe_games = {}
    _memory_games = {}
    _guessnumber_games = {}
    _unscramble_games = {}
    _connect4_games = {}
    _battleship_games = {}
    _minesweeper_games = {}
    _mastermind_games = {}
    _riddles = {}
