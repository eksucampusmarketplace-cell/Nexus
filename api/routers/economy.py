"""Economy router."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routers.auth import get_current_user
from shared.database import get_db
from shared.models import EconomyConfig, Group, Member, Transaction, User, Wallet
from shared.schemas import (
    EconomyConfigResponse,
    TransactionRequest,
    TransactionResponse,
    WalletResponse,
)

router = APIRouter()


@router.get("/groups/{group_id}/economy/config")
async def get_economy_config(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get economy configuration."""
    result = await db.execute(
        select(EconomyConfig).where(EconomyConfig.group_id == group_id)
    )
    config = result.scalar()

    if not config:
        # Return default config
        return EconomyConfigResponse(
            currency_name="coins",
            currency_emoji="🪙",
            earn_per_message=1,
            earn_per_reaction=2,
            daily_bonus=100,
        )

    return config


@router.get("/groups/{group_id}/economy/wallet")
async def get_wallet(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's wallet."""
    # Get member
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get wallet
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet:
        # Create wallet
        wallet = Wallet(
            user_id=current_user.id,
            group_id=group_id,
        )
        db.add(wallet)
        await db.commit()

    return wallet


@router.post("/groups/{group_id}/economy/transfer")
async def transfer_coins(
    group_id: int,
    request: TransactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transfer coins to another user."""
    # Get sender wallet
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    sender_wallet = result.scalar()

    if not sender_wallet:
        raise HTTPException(status_code=400, detail="No wallet found")

    if sender_wallet.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Get recipient wallet
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == request.to_user_id,
            Wallet.group_id == group_id,
        )
    )
    recipient_wallet = result.scalar()

    if not recipient_wallet:
        # Create wallet for recipient
        recipient_wallet = Wallet(
            user_id=request.to_user_id,
            group_id=group_id,
        )
        db.add(recipient_wallet)
        await db.flush()

    # Perform transfer
    sender_wallet.balance -= request.amount
    sender_wallet.total_spent += request.amount
    recipient_wallet.balance += request.amount
    recipient_wallet.total_earned += request.amount

    # Record transaction
    transaction = Transaction(
        from_wallet_id=sender_wallet.id,
        to_wallet_id=recipient_wallet.id,
        amount=request.amount,
        reason=request.reason,
        transaction_type="transfer",
    )
    db.add(transaction)

    await db.commit()

    return {"success": True, "new_balance": sender_wallet.balance}


@router.get("/groups/{group_id}/economy/leaderboard")
async def get_leaderboard(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get economy leaderboard."""
    result = await db.execute(
        select(Wallet, User)
        .join(User, Wallet.user_id == User.id)
        .where(Wallet.group_id == group_id)
        .order_by(Wallet.balance.desc())
        .limit(20)
    )

    leaderboard = [
        {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": wallet.balance,
            "total_earned": wallet.total_earned,
        }
        for wallet, user in result.all()
    ]

    return leaderboard
