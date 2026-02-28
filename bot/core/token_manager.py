"""Token manager for handling multiple bot tokens."""

import hashlib
import os
from dataclasses import dataclass
from typing import Dict, Optional

from aiogram import Bot
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import AsyncSessionLocal
from shared.models import BotInstance


@dataclass
class BotIdentity:
    """Bot identity information."""
    bot_id: int
    username: str
    name: str
    token_hash: str


class TokenManager:
    """Manages multiple bot tokens (shared + custom)."""

    def __init__(self):
        self._bots: Dict[str, Bot] = {}
        self._identities: Dict[str, BotIdentity] = {}
        self._group_to_token: Dict[int, str] = {}
        self._encryption_key = os.getenv("ENCRYPTION_KEY")
        if self._encryption_key:
            self._fernet = Fernet(self._encryption_key.encode())
        else:
            self._fernet = None

    def _hash_token(self, token: str) -> str:
        """Create hash of token for lookup."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _encrypt_token(self, token: str) -> str:
        """Encrypt token for storage."""
        if self._fernet:
            return self._fernet.encrypt(token.encode()).decode()
        return token  # Fallback - not recommended

    def _decrypt_token(self, encrypted: str) -> str:
        """Decrypt token from storage."""
        if self._fernet:
            return self._fernet.decrypt(encrypted.encode()).decode()
        return encrypted

    async def initialize(self) -> None:
        """Load all active bot instances on startup."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BotInstance).where(BotInstance.is_active == True)
            )
            instances = result.scalars().all()

            for instance in instances:
                try:
                    # Decrypt token
                    token = self._decrypt_token(instance.token_hash)

                    # Create bot instance
                    bot = Bot(token=token)
                    bot_info = await bot.get_me()

                    identity = BotIdentity(
                        bot_id=bot_info.id,
                        username=bot_info.username,
                        name=bot_info.first_name,
                        token_hash=self._hash_token(token),
                    )

                    self._bots[identity.token_hash] = bot
                    self._identities[identity.token_hash] = identity
                    self._group_to_token[instance.group_id] = identity.token_hash

                    # Set webhook
                    webhook_url = instance.webhook_url
                    await bot.set_webhook(
                        url=webhook_url,
                        allowed_updates=[
                            "message",
                            "edited_message",
                            "callback_query",
                            "inline_query",
                            "chat_member",
                            "my_chat_member",
                            "poll",
                            "poll_answer",
                            "chat_join_request",
                            "message_reaction",
                        ],
                    )

                except Exception as e:
                    print(f"Failed to initialize bot for group {instance.group_id}: {e}")

    async def register_custom_token(
        self,
        token: str,
        group_id: int,
        registered_by: int,
        webhook_base_url: str,
    ) -> BotIdentity:
        """
        Register a new custom bot token for a group.

        Args:
            token: The bot token from @BotFather
            group_id: The group to associate with this token
            registered_by: User ID who registered the token
            webhook_base_url: Base URL for webhooks

        Returns:
            BotIdentity with bot info
        """
        # Validate token via Telegram API
        try:
            temp_bot = Bot(token=token)
            bot_info = await temp_bot.get_me()
            await temp_bot.session.close()
        except Exception as e:
            raise ValueError(f"Invalid bot token: {e}")

        token_hash = self._hash_token(token)

        # Check if token already registered
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BotInstance).where(BotInstance.token_hash == token_hash)
            )
            if result.scalar():
                raise ValueError("This bot token is already registered")

        # Create webhook URL
        webhook_url = f"{webhook_base_url}/webhook/{token_hash}"

        # Encrypt and store token
        encrypted_token = self._encrypt_token(token)

        # Create bot instance
        bot = Bot(token=token)
        identity = BotIdentity(
            bot_id=bot_info.id,
            username=bot_info.username,
            name=bot_info.first_name,
            token_hash=token_hash,
        )

        # Set up webhook
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=[
                "message",
                "edited_message",
                "callback_query",
                "inline_query",
                "chat_member",
                "my_chat_member",
                "poll",
                "poll_answer",
            ],
        )

        # Store in database
        async with AsyncSessionLocal() as session:
            instance = BotInstance(
                token_hash=encrypted_token,  # Store encrypted
                bot_telegram_id=bot_info.id,
                bot_username=bot_info.username,
                bot_name=bot_info.first_name,
                group_id=group_id,
                registered_by=registered_by,
                is_active=True,
                webhook_url=webhook_url,
            )
            session.add(instance)
            await session.commit()

        # Cache bot instance
        self._bots[token_hash] = bot
        self._identities[token_hash] = identity
        self._group_to_token[group_id] = token_hash

        return identity

    async def revoke_token(self, group_id: int) -> bool:
        """
        Revoke a custom token for a group.

        Args:
            group_id: The group whose token should be revoked

        Returns:
            True if revoked successfully
        """
        token_hash = self._group_to_token.get(group_id)
        if not token_hash:
            return False

        bot = self._bots.get(token_hash)
        if bot:
            try:
                await bot.delete_webhook()
                await bot.session.close()
            except Exception:
                pass

        # Update database
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(BotInstance).where(BotInstance.group_id == group_id)
            )
            instance = result.scalar()
            if instance:
                instance.is_active = False
                await session.commit()

        # Remove from cache
        del self._bots[token_hash]
        del self._identities[token_hash]
        del self._group_to_token[group_id]

        return True

    def get_bot(self, token_hash: str) -> Optional[Bot]:
        """Get bot instance by token hash."""
        return self._bots.get(token_hash)

    def get_bot_for_group(self, group_id: int) -> Optional[Bot]:
        """Get bot instance for a group."""
        token_hash = self._group_to_token.get(group_id)
        if token_hash:
            return self._bots.get(token_hash)
        return None

    def get_identity(self, token_hash: str) -> Optional[BotIdentity]:
        """Get bot identity by token hash."""
        return self._identities.get(token_hash)

    def get_identity_for_group(self, group_id: int) -> Optional[BotIdentity]:
        """Get bot identity for a group."""
        token_hash = self._group_to_token.get(group_id)
        if token_hash:
            return self._identities.get(token_hash)
        return None

    def get_group_id_for_token(self, token_hash: str) -> Optional[int]:
        """Get group ID associated with a token hash."""
        for gid, th in self._group_to_token.items():
            if th == token_hash:
                return gid
        return None

    async def get_all_active_bots(self) -> Dict[str, Bot]:
        """Get all active bot instances."""
        return self._bots.copy()

    async def cleanup(self) -> None:
        """Close all bot sessions."""
        for bot in self._bots.values():
            try:
                await bot.session.close()
            except Exception:
                pass
        self._bots.clear()
        self._identities.clear()
        self._group_to_token.clear()


# Global token manager instance
token_manager = TokenManager()
