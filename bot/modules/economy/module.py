"""Economy module - Virtual currency system with wallets, transactions, shop, games."""

import random
import re
from datetime import datetime, timedelta
from typing import Optional

from aiogram.types import Message, CallbackQuery
from pydantic import BaseModel

from bot.core.context import NexusContext
from bot.core.module_base import CommandDef, ModuleCategory, NexusModule


class EconomyConfig(BaseModel):
    """Configuration for economy module."""
    currency_name: str = "coins"
    currency_emoji: str = "🪙"
    earn_per_message: int = 1
    earn_per_reaction: int = 2
    daily_bonus: int = 100
    work_cooldown: int = 3600  # seconds
    crime_cooldown: int = 1800  # seconds
    daily_cooldown: int = 86400  # seconds
    xp_to_coin_enabled: bool = False
    bank_interest_rate: float = 0.05  # 5% daily
    tax_rate: float = 0.0  # 0% tax on transfers
    min_transfer: int = 1
    max_transfer: int = 1000000


class EconomyModule(NexusModule):
    """Virtual currency system with wallet, bank, shop, and games."""

    name = "economy"
    version = "1.0.0"
    author = "Nexus Team"
    description = "Complete economy system with currency, bank, shop, and games"
    category = ModuleCategory.COMMUNITY

    config_schema = EconomyConfig
    default_config = EconomyConfig().dict()

    commands = [
        CommandDef(
            name="balance",
            description="Check wallet balance",
            admin_only=False,
            aliases=["bal", "wallet"],
        ),
        CommandDef(
            name="daily",
            description="Claim daily bonus coins",
            admin_only=False,
        ),
        CommandDef(
            name="give",
            description="Give coins to another user",
            admin_only=False,
            aliases=["transfer", "pay"],
        ),
        CommandDef(
            name="leaderboard",
            description="View economy leaderboard",
            admin_only=False,
            aliases=["lb", "rich"],
        ),
        CommandDef(
            name="transactions",
            description="View recent transactions",
            admin_only=False,
            aliases=["tx"],
        ),
        CommandDef(
            name="shop",
            description="View group shop",
            admin_only=False,
        ),
        CommandDef(
            name="buy",
            description="Purchase item from shop",
            admin_only=False,
        ),
        CommandDef(
            name="inventory",
            description="View your inventory",
            admin_only=False,
            aliases=["inv"],
        ),
        CommandDef(
            name="coinflip",
            description="Flip a coin and bet coins",
            admin_only=False,
        ),
        CommandDef(
            name="gamble",
            description="Gamble coins (50/50 chance)",
            admin_only=False,
        ),
        CommandDef(
            name="rob",
            description="Attempt to rob another user",
            admin_only=False,
        ),
        CommandDef(
            name="beg",
            description="Beg for coins",
            admin_only=False,
        ),
        CommandDef(
            name="work",
            description="Work to earn coins",
            admin_only=False,
        ),
        CommandDef(
            name="crime",
            description="Commit a crime for big reward or punishment",
            admin_only=False,
        ),
        CommandDef(
            name="deposit",
            description="Deposit coins to bank",
            admin_only=False,
        ),
        CommandDef(
            name="withdraw",
            description="Withdraw coins from bank",
            admin_only=False,
        ),
        CommandDef(
            name="bank",
            description="View bank balance",
            admin_only=False,
        ),
        CommandDef(
            name="loan",
            description="Take a loan from the bank",
            admin_only=False,
        ),
        CommandDef(
            name="repay",
            description="Repay your loan",
            admin_only=False,
        ),
    ]

    async def on_load(self, app):
        """Register command handlers."""
        self.register_command("balance", self.cmd_balance)
        self.register_command("bal", self.cmd_balance)
        self.register_command("wallet", self.cmd_balance)
        self.register_command("daily", self.cmd_daily)
        self.register_command("give", self.cmd_give)
        self.register_command("transfer", self.cmd_give)
        self.register_command("pay", self.cmd_give)
        self.register_command("leaderboard", self.cmd_leaderboard)
        self.register_command("lb", self.cmd_leaderboard)
        self.register_command("rich", self.cmd_leaderboard)
        self.register_command("transactions", self.cmd_transactions)
        self.register_command("tx", self.cmd_transactions)
        self.register_command("shop", self.cmd_shop)
        self.register_command("buy", self.cmd_buy)
        self.register_command("inventory", self.cmd_inventory)
        self.register_command("inv", self.cmd_inventory)
        self.register_command("coinflip", self.cmd_coinflip)
        self.register_command("gamble", self.cmd_gamble)
        self.register_command("rob", self.cmd_rob)
        self.register_command("beg", self.cmd_beg)
        self.register_command("work", self.cmd_work)
        self.register_command("crime", self.cmd_crime)
        self.register_command("deposit", self.cmd_deposit)
        self.register_command("withdraw", self.cmd_withdraw)
        self.register_command("bank", self.cmd_bank)
        self.register_command("loan", self.cmd_loan)
        self.register_command("repay", self.cmd_repay)

    async def on_message(self, ctx: NexusContext):
        """Award coins for messages."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        await self._award_coins(ctx, config.earn_per_message, "message")

    def _get_user_id(self, ctx: NexusContext, args: list) -> Optional[int]:
        """Extract user ID from message or args."""
        # Try reply first
        if ctx.replied_to and ctx.replied_to.from_user:
            return ctx.replied_to.from_user.id

        # Try mention
        if ctx.message.entities:
            for entity in ctx.message.entities:
                if entity.type == "text_mention":
                    return entity.user.id

        # Try username
        text = ctx.message.text or ""
        if args:
            username = args[0].lstrip("@")
            if username:
                if ctx.db:
                    from shared.models import User
                    result = ctx.db.execute(
                        f"SELECT telegram_id FROM users WHERE username = '{username}' LIMIT 1"
                    )
                    row = result.fetchone()
                    if row:
                        return row[0]

        return None

    async def _get_wallet(self, ctx: NexusContext, user_id: int):
        """Get or create wallet for user."""
        from shared.models import Wallet

        # Get user ID from telegram_id
        result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {user_id} LIMIT 1"
        )
        user_db_id = result.scalar()

        if not user_db_id:
            return None

        # Get or create wallet
        result = ctx.db.execute(
            f"""
            SELECT id, balance, bank_balance, loan_amount, last_daily, last_work, last_crime
            FROM wallets
            WHERE user_id = {user_db_id} AND group_id = {ctx.group.id}
            LIMIT 1
            """
        )
        row = result.fetchone()

        if not row:
            wallet = Wallet(
                user_id=user_db_id,
                group_id=ctx.group.id,
                balance=0,
                bank_balance=0,
                loan_amount=0,
                total_earned=0,
                total_spent=0,
            )
            ctx.db.add(wallet)
            ctx.db.commit()
            return wallet

        from dataclasses import dataclass

        @dataclass
        class WalletData:
            id: int
            balance: int
            bank_balance: int
            loan_amount: int
            last_daily: Optional[datetime]
            last_work: Optional[datetime]
            last_crime: Optional[datetime]

        return WalletData(*row)

    async def _award_coins(self, ctx: NexusContext, amount: int, reason: str):
        """Award coins to user."""
        if amount <= 0:
            return

        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        if wallet:
            from shared.models import Wallet, Transaction

            user_result = ctx.db.execute(
                f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
            )
            user_id = user_result.scalar()

            # Update wallet
            ctx.db.execute(
                f"""
                UPDATE wallets
                SET balance = balance + {amount},
                    total_earned = total_earned + {amount}
                WHERE user_id = {user_id} AND group_id = {ctx.group.id}
                """
            )

            # Add transaction
            transaction = Transaction(
                from_wallet_id=wallet.id,
                to_wallet_id=wallet.id,
                amount=amount,
                reason=reason,
                transaction_type="earned",
            )
            ctx.db.add(transaction)
            ctx.db.commit()

    async def _check_cooldown(self, ctx: NexusContext, cooldown_field: str, cooldown_seconds: int):
        """Check if user is on cooldown."""
        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        if not wallet:
            return True  # No wallet means can proceed

        last_time = getattr(wallet, cooldown_field, None)
        if last_time:
            elapsed = (datetime.utcnow() - last_time).total_seconds()
            if elapsed < cooldown_seconds:
                remaining = int(cooldown_seconds - elapsed)
                return remaining

        return False

    async def cmd_balance(self, ctx: NexusContext):
        """Check wallet balance."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        # Check if checking someone else's balance
        target_id = ctx.user.telegram_id
        if args:
            user_id = self._get_user_id(ctx, args)
            if user_id:
                target_id = user_id

        wallet = await self._get_wallet(ctx, target_id)
        if not wallet:
            await ctx.reply(f"💰 No wallet found")
            return

        text = f"💰 {config.currency_name.capitalize()} Balance\n\n"
        text += f"Wallet: {wallet.balance:,} {config.currency_emoji}\n"
        text += f"Bank: {wallet.bank_balance:,} {config.currency_emoji}\n"
        if wallet.loan_amount > 0:
            text += f"Loan: -{wallet.loan_amount:,} {config.currency_emoji}\n"
        text += f"Total: {wallet.balance + wallet.bank_balance - wallet.loan_amount:,} {config.currency_emoji}"

        await ctx.reply(text)

    async def cmd_daily(self, ctx: NexusContext):
        """Claim daily bonus."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))

        cooldown = await self._check_cooldown(ctx, "last_daily", config.daily_cooldown)
        if cooldown:
            hours = cooldown // 3600
            minutes = (cooldown % 3600) // 60
            await ctx.reply(
                f"⏰ You already claimed your daily bonus!\n"
                f"Come back in {hours}h {minutes}m"
            )
            return

        await self._award_coins(ctx, config.daily_bonus, "daily bonus")

        # Update last_daily
        from shared.models import Wallet
        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        ctx.db.execute(
            f"""
            UPDATE wallets
            SET last_daily = NOW()
            WHERE user_id = {user_id} AND group_id = {ctx.group.id}
            """
        )
        ctx.db.commit()

        await ctx.reply(
            f"🎁 Daily Bonus Claimed!\n"
            f"+{config.daily_bonus:,} {config.currency_emoji}"
        )

    async def cmd_give(self, ctx: NexusContext):
        """Give coins to another user."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply(
                f"❌ Usage: /give @{username} <amount> [reason]\n"
                f"Example: /give @username 100 thanks for help"
            )
            return

        target_id = self._get_user_id(ctx, args)
        if not target_id:
            await ctx.reply("❌ User not found")
            return

        if target_id == ctx.user.telegram_id:
            await ctx.reply("❌ You can't give coins to yourself!")
            return

        try:
            amount = int(args[1])
        except ValueError:
            await ctx.reply("❌ Invalid amount")
            return

        if amount < config.min_transfer:
            await ctx.reply(f"❌ Minimum transfer is {config.min_transfer:,} {config.currency_emoji}")
            return

        if amount > config.max_transfer:
            await ctx.reply(f"❌ Maximum transfer is {config.max_transfer:,} {config.currency_emoji}")
            return

        # Check sender's balance
        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        if not wallet or wallet.balance < amount:
            await ctx.reply(f"❌ You don't have enough {config.currency_name}!")
            return

        # Calculate tax
        tax = int(amount * config.tax_rate)
        actual_amount = amount - tax

        # Get wallets
        from shared.models import Wallet, Transaction

        sender_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        sender_id = sender_result.scalar()

        target_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {target_id} LIMIT 1"
        )
        target_user_id = target_result.scalar()

        # Get wallet IDs
        sender_wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        target_wallet = await self._get_wallet(ctx, target_id)

        reason = " ".join(args[2:]) if len(args) > 2 else "transfer"

        # Transfer coins
        ctx.db.execute(
            f"""
            UPDATE wallets
            SET balance = balance - {amount},
                total_spent = total_spent + {amount}
            WHERE user_id = {sender_id} AND group_id = {ctx.group.id}
            """
        )

        ctx.db.execute(
            f"""
            UPDATE wallets
            SET balance = balance + {actual_amount},
                total_earned = total_earned + {actual_amount}
            WHERE user_id = {target_user_id} AND group_id = {ctx.group.id}
            """
        )

        # Add transactions
        transaction_out = Transaction(
            from_wallet_id=sender_wallet.id,
            to_wallet_id=target_wallet.id,
            amount=amount,
            reason=f"{reason} (tax: {tax})",
            transaction_type="transfer",
        )
        ctx.db.add(transaction_out)

        transaction_in = Transaction(
            from_wallet_id=sender_wallet.id,
            to_wallet_id=target_wallet.id,
            amount=actual_amount,
            reason=reason,
            transaction_type="received",
        )
        ctx.db.add(transaction_in)

        ctx.db.commit()

        await ctx.reply(
            f"💸 Transfer Successful!\n\n"
            f"Sent: {amount:,} {config.currency_emoji}\n"
            f"Tax: {tax:,} {config.currency_emoji}\n"
            f"Received: {actual_amount:,} {config.currency_emoji}"
        )

    async def cmd_leaderboard(self, ctx: NexusContext):
        """View economy leaderboard."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))

        from shared.models import Wallet, User

        result = ctx.db.execute(
            f"""
            SELECT u.username, u.first_name, u.last_name, w.balance + w.bank_balance - w.loan_amount as total
            FROM wallets w
            JOIN users u ON w.user_id = u.id
            WHERE w.group_id = {ctx.group.id}
            ORDER BY total DESC
            LIMIT 10
            """
        )

        leaders = result.fetchall()
        if not leaders:
            await ctx.reply("❌ No wallets yet")
            return

        text = f"🏆 {config.currency_name.capitalize()} Leaderboard\n\n"
        for i, row in enumerate(leaders, 1):
            username = row[0]
            name = f"{row[1]} {row[2] or ''}".strip()
            display_name = username or name
            amount = row[3]

            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {display_name}: {amount:,} {config.currency_emoji}\n"

        await ctx.reply(text)

    async def cmd_transactions(self, ctx: NexusContext):
        """View recent transactions."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))

        from shared.models import Transaction, Wallet, User

        result = ctx.db.execute(
            f"""
            SELECT t.amount, t.reason, t.transaction_type, t.created_at,
                   u1.username, u1.first_name, u1.last_name,
                   u2.username, u2.first_name, u2.last_name
            FROM transactions t
            JOIN wallets w1 ON t.from_wallet_id = w1.id
            JOIN wallets w2 ON t.to_wallet_id = w2.id
            JOIN users u1 ON w1.user_id = u1.id
            JOIN users u2 ON w2.user_id = u2.id
            WHERE w1.group_id = {ctx.group.id}
              AND (w1.user_id = (SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id})
                   OR w2.user_id = (SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id}))
            ORDER BY t.created_at DESC
            LIMIT 10
            """
        )

        transactions = result.fetchall()
        if not transactions:
            await ctx.reply("❌ No recent transactions")
            return

        text = "💳 Recent Transactions\n\n"
        for row in transactions:
            amount = row[0]
            reason = row[1]
            trans_type = row[2]
            created = row[3].strftime("%Y-%m-%d %H:%M")
            from_user = row[4] or f"{row[5]} {row[6] or ''}".strip()
            to_user = row[7] or f"{row[8]} {row[9] or ''}".strip()

            icon = "💸" if trans_type == "transfer" else "💰" if trans_type == "earned" else "💳"
            text += f"{icon} {created}\n"
            text += f"{from_user} → {to_user}\n"
            text += f"{amount:,} {config.currency_emoji} - {reason}\n\n"

        await ctx.reply(text)

    async def cmd_shop(self, ctx: NexusContext):
        """View group shop."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))

        # For now, show default shop items
        # In production, this would be configurable
        items = [
            {"name": "VIP Badge", "price": 1000, "emoji": "⭐"},
            {"name": "Gold Badge", "price": 5000, "emoji": "🌟"},
            {"name": "Diamond Badge", "price": 10000, "emoji": "💎"},
            {"name": "Custom Title (7 days)", "price": 5000, "emoji": "🏷️"},
            {"name": "Mute Protection (24h)", "price": 2000, "emoji": "🔇"},
        ]

        text = f"🏪 Group Shop\n\nUse /buy <item> to purchase\n\n"
        for item in items:
            text += f"{item['emoji']} {item['name']} - {item['price']:,} {config.currency_emoji}\n"

        await ctx.reply(text)

    async def cmd_buy(self, ctx: NexusContext):
        """Purchase item from shop."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /buy <item>")
            return

        item_name = " ".join(args)

        # Simple item lookup (in production, would use DB)
        items = {
            "VIP Badge": 1000,
            "Gold Badge": 5000,
            "Diamond Badge": 10000,
            "Custom Title": 5000,
            "Mute Protection": 2000,
        }

        price = items.get(item_name)
        if not price:
            await ctx.reply("❌ Item not found")
            return

        # Check balance
        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        if not wallet or wallet.balance < price:
            await ctx.reply(f"❌ You don't have enough {config.currency_name}!")
            return

        # Purchase item
        from shared.models import Wallet, Transaction

        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        ctx.db.execute(
            f"""
            UPDATE wallets
            SET balance = balance - {price},
                total_spent = total_spent + {price}
            WHERE user_id = {user_id} AND group_id = {ctx.group.id}
            """
        )

        # Add transaction
        transaction = Transaction(
            from_wallet_id=wallet.id,
            to_wallet_id=wallet.id,
            amount=price,
            reason=f"Purchased: {item_name}",
            transaction_type="purchase",
        )
        ctx.db.add(transaction)
        ctx.db.commit()

        await ctx.reply(f"✅ Purchased: {item_name}\n-{price:,} {config.currency_emoji}")

    async def cmd_inventory(self, ctx: NexusContext):
        """View your inventory."""
        # For now, show a placeholder
        # In production, would track items in DB
        await ctx.reply("📦 Your inventory is empty.\n\nUse /shop to see available items!")

    async def cmd_coinflip(self, ctx: NexusContext):
        """Flip a coin and bet coins."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if len(args) < 2:
            await ctx.reply("❌ Usage: /coinflip <amount> <heads|tails>")
            return

        try:
            amount = int(args[0])
        except ValueError:
            await ctx.reply("❌ Invalid amount")
            return

        choice = args[1].lower()
        if choice not in ["heads", "tails"]:
            await ctx.reply("❌ Choose: heads or tails")
            return

        if amount <= 0:
            await ctx.reply("❌ Amount must be positive")
            return

        # Check balance
        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        if not wallet or wallet.balance < amount:
            await ctx.reply(f"❌ You don't have enough {config.currency_name}!")
            return

        # Flip coin
        result = random.choice(["heads", "tails"])
        won = result == choice

        # Update balance
        from shared.models import Wallet, Transaction

        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        if won:
            winnings = amount * 2
            ctx.db.execute(
                f"""
                UPDATE wallets
                SET balance = balance + {amount},
                    total_earned = total_earned + {amount}
                WHERE user_id = {user_id} AND group_id = {ctx.group.id}
                """
            )
            await ctx.reply(
                f"🪙 Coin flip result: {result}!\n"
                f"🎉 You won {winnings:,} {config.currency_emoji}!"
            )
        else:
            ctx.db.execute(
                f"""
                UPDATE wallets
                SET balance = balance - {amount},
                    total_spent = total_spent + {amount}
                WHERE user_id = {user_id} AND group_id = {ctx.group.id}
                """
            )
            await ctx.reply(
                f"🪙 Coin flip result: {result}\n"
                f"😢 You lost {amount:,} {config.currency_emoji}"
            )

        # Add transaction
        transaction = Transaction(
            from_wallet_id=wallet.id,
            to_wallet_id=wallet.id,
            amount=winnings if won else -amount,
            reason=f"coinflip ({result})",
            transaction_type="gamble",
        )
        ctx.db.add(transaction)
        ctx.db.commit()

    async def cmd_gamble(self, ctx: NexusContext):
        """Gamble coins (50/50 chance to double or lose)."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /gamble <amount>")
            return

        try:
            amount = int(args[0])
        except ValueError:
            await ctx.reply("❌ Invalid amount")
            return

        if amount <= 0:
            await ctx.reply("❌ Amount must be positive")
            return

        # Check balance
        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        if not wallet or wallet.balance < amount:
            await ctx.reply(f"❌ You don't have enough {config.currency_name}!")
            return

        # 50/50 chance
        won = random.random() < 0.5

        # Update balance
        from shared.models import Wallet, Transaction

        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        if won:
            winnings = amount * 2
            ctx.db.execute(
                f"""
                UPDATE wallets
                SET balance = balance + {amount},
                    total_earned = total_earned + {amount}
                WHERE user_id = {user_id} AND group_id = {ctx.group.id}
                """
            )
            await ctx.reply(
                f"🎰 You won!\n"
                f"💰 +{winnings:,} {config.currency_emoji}"
            )
        else:
            ctx.db.execute(
                f"""
                UPDATE wallets
                SET balance = balance - {amount},
                    total_spent = total_spent + {amount}
                WHERE user_id = {user_id} AND group_id = {ctx.group.id}
                """
            )
            await ctx.reply(
                f"🎰 You lost!\n"
                f"💸 -{amount:,} {config.currency_emoji}"
            )

        # Add transaction
        transaction = Transaction(
            from_wallet_id=wallet.id,
            to_wallet_id=wallet.id,
            amount=winnings if won else -amount,
            reason="gamble",
            transaction_type="gamble",
        )
        ctx.db.add(transaction)
        ctx.db.commit()

    async def cmd_rob(self, ctx: NexusContext):
        """Attempt to rob another user."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        target_id = self._get_user_id(ctx, args)
        if not target_id:
            await ctx.reply("❌ User not found")
            return

        if target_id == ctx.user.telegram_id:
            await ctx.reply("❌ You can't rob yourself!")
            return

        # Check target's balance
        target_wallet = await self._get_wallet(ctx, target_id)
        if not target_wallet or target_wallet.balance < 100:
            await ctx.reply("❌ User doesn't have enough coins to rob!")
            return

        # Low success rate (20%)
        success = random.random() < 0.2

        # Rob amount (10-30% of target's balance)
        rob_amount = int(target_wallet.balance * random.uniform(0.1, 0.3))

        if success:
            # Successful rob
            from shared.models import Wallet, Transaction

            attacker_result = ctx.db.execute(
                f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
            )
            attacker_id = attacker_result.scalar()

            target_result = ctx.db.execute(
                f"SELECT id FROM users WHERE telegram_id = {target_id} LIMIT 1"
            )
            target_user_id = target_result.scalar()

            # Transfer coins
            ctx.db.execute(
                f"""
                UPDATE wallets
                SET balance = balance - {rob_amount},
                    total_spent = total_spent + {rob_amount}
                WHERE user_id = {target_user_id} AND group_id = {ctx.group.id}
                """
            )

            ctx.db.execute(
                f"""
                UPDATE wallets
                SET balance = balance + {rob_amount},
                    total_earned = total_earned + {rob_amount}
                WHERE user_id = {attacker_id} AND group_id = {ctx.group.id}
                """
            )

            ctx.db.commit()

            await ctx.reply(
                f"🦹 Successful heist!\n"
                f"💰 You stole {rob_amount:,} {config.currency_emoji}!"
            )
        else:
            # Failed rob - lose 10% of what you tried to steal
            fine = int(rob_amount * 0.1)

            attacker_result = ctx.db.execute(
                f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
            )
            attacker_id = attacker_result.scalar()

            ctx.db.execute(
                f"""
                UPDATE wallets
                SET balance = balance - {fine},
                    total_spent = total_spent + {fine}
                WHERE user_id = {attacker_id} AND group_id = {ctx.group.id}
                """
            )

            ctx.db.commit()

            await ctx.reply(
                f"🚔 You got caught!\n"
                f"💸 You paid a fine of {fine:,} {config.currency_emoji}"
            )

    async def cmd_beg(self, ctx: NexusContext):
        """Beg for coins."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))

        # Small chance (30%) to get coins
        if random.random() < 0.3:
            amount = random.randint(1, 50)
            await self._award_coins(ctx, amount, "begging")
            await ctx.reply(
                f"🤷 Someone gave you {amount:,} {config.currency_emoji}!\n"
                f"Total: +{amount:,} {config.currency_emoji}"
            )
        else:
            await ctx.reply("😢 No one gave you anything. Try again later!")

    async def cmd_work(self, ctx: NexusContext):
        """Work to earn coins."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))

        cooldown = await self._check_cooldown(ctx, "last_work", config.work_cooldown)
        if cooldown:
            minutes = cooldown // 60
            await ctx.reply(
                f"⏰ You're tired!\n"
                f"Come back in {minutes} minutes to work again."
            )
            return

        # Earn random amount (10-100 coins)
        amount = random.randint(10, 100)
        await self._award_coins(ctx, amount, "work")

        # Update last_work
        from shared.models import Wallet
        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        ctx.db.execute(
            f"""
            UPDATE wallets
            SET last_work = NOW()
            WHERE user_id = {user_id} AND group_id = {ctx.group.id}
            """
        )
        ctx.db.commit()

        await ctx.reply(
            f"💼 Work completed!\n"
            f"💰 You earned {amount:,} {config.currency_emoji}"
        )

    async def cmd_crime(self, ctx: NexusContext):
        """Commit a crime for big reward or punishment."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))

        cooldown = await self._check_cooldown(ctx, "last_crime", config.crime_cooldown)
        if cooldown:
            minutes = cooldown // 60
            await ctx.reply(
                f"⏰ You're cooling down!\n"
                f"Come back in {minutes} minutes."
            )
            return

        # 40% success, 60% fail
        success = random.random() < 0.4

        if success:
            # Big reward (200-1000 coins)
            amount = random.randint(200, 1000)
            await self._award_coins(ctx, amount, "crime")

            await ctx.reply(
                f"🏦 Successful heist!\n"
                f"💰 You escaped with {amount:,} {config.currency_emoji}!"
            )
        else:
            # Big punishment (lose 100-500 coins)
            fine = random.randint(100, 500)

            wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
            if wallet and wallet.balance >= fine:
                from shared.models import Wallet

                user_result = ctx.db.execute(
                    f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
                )
                user_id = user_result.scalar()

                ctx.db.execute(
                    f"""
                    UPDATE wallets
                    SET balance = balance - {fine},
                        total_spent = total_spent + {fine}
                    WHERE user_id = {user_id} AND group_id = {ctx.group.id}
                    """
                )
                ctx.db.commit()

            await ctx.reply(
                f"🚔 You got caught!\n"
                f"💸 You had to pay {fine:,} {config.currency_emoji} in fines."
            )

        # Update last_crime
        from shared.models import Wallet
        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        ctx.db.execute(
            f"""
            UPDATE wallets
            SET last_crime = NOW()
            WHERE user_id = {user_id} AND group_id = {ctx.group.id}
            """
        )
        ctx.db.commit()

    async def cmd_deposit(self, ctx: NexusContext):
        """Deposit coins to bank."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /deposit <amount>")
            return

        try:
            amount = int(args[0])
        except ValueError:
            await ctx.reply("❌ Invalid amount")
            return

        if amount <= 0:
            await ctx.reply("❌ Amount must be positive")
            return

        # Check balance
        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        if not wallet or wallet.balance < amount:
            await ctx.reply(f"❌ You don't have enough {config.currency_name}!")
            return

        # Deposit to bank
        from shared.models import Wallet, Transaction

        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        ctx.db.execute(
            f"""
            UPDATE wallets
            SET balance = balance - {amount},
                bank_balance = bank_balance + {amount}
            WHERE user_id = {user_id} AND group_id = {ctx.group.id}
            """
        )

        # Add transaction
        transaction = Transaction(
            from_wallet_id=wallet.id,
            to_wallet_id=wallet.id,
            amount=amount,
            reason="bank deposit",
            transaction_type="deposit",
        )
        ctx.db.add(transaction)
        ctx.db.commit()

        await ctx.reply(
            f"🏦 Deposited {amount:,} {config.currency_emoji} to bank\n"
            f"💰 Your coins are now safe from robbery!"
        )

    async def cmd_withdraw(self, ctx: NexusContext):
        """Withdraw coins from bank."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /withdraw <amount>")
            return

        try:
            amount = int(args[0])
        except ValueError:
            await ctx.reply("❌ Invalid amount")
            return

        if amount <= 0:
            await ctx.reply("❌ Amount must be positive")
            return

        # Check bank balance
        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        if not wallet or wallet.bank_balance < amount:
            await ctx.reply(f"❌ You don't have enough {config.currency_name} in the bank!")
            return

        # Withdraw from bank
        from shared.models import Wallet, Transaction

        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        ctx.db.execute(
            f"""
            UPDATE wallets
            SET balance = balance + {amount},
                bank_balance = bank_balance - {amount}
            WHERE user_id = {user_id} AND group_id = {ctx.group.id}
            """
        )

        # Add transaction
        transaction = Transaction(
            from_wallet_id=wallet.id,
            to_wallet_id=wallet.id,
            amount=amount,
            reason="bank withdrawal",
            transaction_type="withdrawal",
        )
        ctx.db.add(transaction)
        ctx.db.commit()

        await ctx.reply(
            f"🏦 Withdrew {amount:,} {config.currency_emoji} from bank\n"
            f"💰 Coins are now in your wallet"
        )

    async def cmd_bank(self, ctx: NexusContext):
        """View bank balance."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))

        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        if not wallet:
            await ctx.reply("❌ No wallet found")
            return

        text = f"🏦 Bank Account\n\n"
        text += f"Balance: {wallet.bank_balance:,} {config.currency_emoji}\n"

        # Calculate daily interest
        daily_interest = int(wallet.bank_balance * config.bank_interest_rate)
        text += f"Daily Interest: +{daily_interest:,} {config.currency_emoji} ({int(config.bank_interest_rate * 100)}%)\n"

        if wallet.loan_amount > 0:
            text += f"\nLoan: -{wallet.loan_amount:,} {config.currency_emoji}\n"

        text += f"\nTotal: {wallet.bank_balance - wallet.loan_amount:,} {config.currency_emoji}"

        await ctx.reply(text)

    async def cmd_loan(self, ctx: NexusContext):
        """Take a loan from the bank."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        if not args:
            await ctx.reply("❌ Usage: /loan <amount>")
            return

        try:
            amount = int(args[0])
        except ValueError:
            await ctx.reply("❌ Invalid amount")
            return

        if amount <= 0:
            await ctx.reply("❌ Amount must be positive")
            return

        # Max loan is 10x current balance
        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)
        max_loan = (wallet.balance + wallet.bank_balance) * 10

        if amount > max_loan:
            await ctx.reply(f"❌ Maximum loan is {max_loan:,} {config.currency_emoji}")
            return

        # Add loan
        from shared.models import Wallet, Transaction

        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        ctx.db.execute(
            f"""
            UPDATE wallets
            SET bank_balance = bank_balance + {amount},
                loan_amount = loan_amount + {amount}
            WHERE user_id = {user_id} AND group_id = {ctx.group.id}
            """
        )

        # Add transaction
        transaction = Transaction(
            from_wallet_id=wallet.id,
            to_wallet_id=wallet.id,
            amount=amount,
            reason="loan",
            transaction_type="loan",
        )
        ctx.db.add(transaction)
        ctx.db.commit()

        await ctx.reply(
            f"🏦 Loan approved!\n"
            f"💰 +{amount:,} {config.currency_emoji}\n"
            f"⚠️ Total loan: {wallet.loan_amount + amount:,} {config.currency_emoji}\n"
            f"Use /repay to pay it back."
        )

    async def cmd_repay(self, ctx: NexusContext):
        """Repay your loan."""
        config = EconomyConfig(**ctx.group.module_configs.get("economy", {}))
        args = ctx.message.text.split()[1:] if ctx.message.text else []

        wallet = await self._get_wallet(ctx, ctx.user.telegram_id)

        if wallet.loan_amount <= 0:
            await ctx.reply("✅ You don't have any loans to repay!")
            return

        # Repay all if no amount specified
        amount = wallet.loan_amount
        if args:
            try:
                amount = int(args[0])
            except ValueError:
                await ctx.reply("❌ Invalid amount")
                return

        if amount > wallet.loan_amount:
            amount = wallet.loan_amount

        # Check balance
        if wallet.balance < amount:
            await ctx.reply(f"❌ You don't have enough {config.currency_name}!")
            return

        # Repay loan
        from shared.models import Wallet, Transaction

        user_result = ctx.db.execute(
            f"SELECT id FROM users WHERE telegram_id = {ctx.user.telegram_id} LIMIT 1"
        )
        user_id = user_result.scalar()

        ctx.db.execute(
            f"""
            UPDATE wallets
            SET balance = balance - {amount},
                loan_amount = loan_amount - {amount}
            WHERE user_id = {user_id} AND group_id = {ctx.group.id}
            """
        )

        # Add transaction
        transaction = Transaction(
            from_wallet_id=wallet.id,
            to_wallet_id=wallet.id,
            amount=amount,
            reason="loan repayment",
            transaction_type="repayment",
        )
        ctx.db.add(transaction)
        ctx.db.commit()

        await ctx.reply(
            f"🏦 Loan repayment successful!\n"
            f"💰 -{amount:,} {config.currency_emoji}\n"
            f"✅ Remaining loan: {wallet.loan_amount - amount:,} {config.currency_emoji}"
        )
