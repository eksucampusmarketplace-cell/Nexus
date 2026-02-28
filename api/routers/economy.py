"""Economy router - Full economy system API."""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
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


# Request/Response models
class EconomyConfigUpdate(BaseModel):
    currency_name: Optional[str] = None
    currency_emoji: Optional[str] = None
    earn_per_message: Optional[int] = None
    earn_per_reaction: Optional[int] = None
    daily_bonus: Optional[int] = None
    work_cooldown: Optional[int] = None
    crime_cooldown: Optional[int] = None
    daily_cooldown: Optional[int] = None
    xp_to_coin_enabled: Optional[bool] = None
    bank_interest_rate: Optional[float] = None
    tax_rate: Optional[float] = None
    min_transfer: Optional[int] = None
    max_transfer: Optional[int] = None


class DailyBonusResponse(BaseModel):
    bonus: int
    new_balance: int
    next_available: str
    streak: int = 0


class WorkResponse(BaseModel):
    earned: int
    new_balance: int
    next_available: str


class GambleRequest(BaseModel):
    amount: int
    choice: str  # "heads" or "tails"


class GambleResponse(BaseModel):
    won: bool
    amount: int
    new_balance: int
    result: str


class RobRequest(BaseModel):
    target_user_id: int


class RobResponse(BaseModel):
    success: bool
    amount: int
    new_balance: int
    message: str


class BankOperationRequest(BaseModel):
    amount: int


class BankResponse(BaseModel):
    balance: int
    bank_balance: int
    total_assets: int


class LoanRequest(BaseModel):
    amount: int


class LoanResponse(BaseModel):
    loan_amount: int
    new_balance: int
    monthly_payment: int


class InventoryItem(BaseModel):
    id: int
    item_name: str
    quantity: int
    purchase_price: int


class ShopItem(BaseModel):
    id: int
    name: str
    description: str
    price: int
    emoji: str
    category: str
    stock: Optional[int] = None


class TransactionHistoryResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int


class EconomyStatsResponse(BaseModel):
    total_supply: int
    total_transactions: int
    total_wallets: int
    daily_volume: int
    richest_user: Optional[dict] = None


# === Configuration ===

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
        return EconomyConfigResponse(
            currency_name="coins",
            currency_emoji="🪙",
            earn_per_message=1,
            earn_per_reaction=2,
            daily_bonus=100,
        )

    return config


@router.patch("/groups/{group_id}/economy/config")
async def update_economy_config(
    group_id: int,
    config_update: EconomyConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update economy configuration (admin only)."""
    # Check admin permission
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    member = result.scalar()

    if not member or member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(
        select(EconomyConfig).where(EconomyConfig.group_id == group_id)
    )
    config = result.scalar()

    if not config:
        config = EconomyConfig(group_id=group_id)
        db.add(config)

    # Update fields
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return config


# === Wallet & Balance ===

@router.get("/groups/{group_id}/economy/wallet")
async def get_wallet(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's wallet (balance, bank, etc.)."""
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=404, detail="Member not found")

    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet:
        wallet = Wallet(
            user_id=current_user.id,
            group_id=group_id,
        )
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)

    return {
        "id": wallet.id,
        "balance": wallet.balance,
        "bank_balance": wallet.bank_balance,
        "loan_amount": wallet.loan_amount,
        "total_earned": wallet.total_earned,
        "total_spent": wallet.total_spent,
        "last_daily": wallet.last_daily.isoformat() if wallet.last_daily else None,
        "last_work": wallet.last_work.isoformat() if wallet.last_work else None,
        "last_crime": wallet.last_crime.isoformat() if wallet.last_crime else None,
    }


@router.get("/groups/{group_id}/economy/wallet/{user_id}")
async def get_user_wallet(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get another user's wallet (limited info)."""
    result = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.group_id == group_id,
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=403, detail="Member not found")

    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == user_id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Get user info
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar()

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
        },
        "balance": wallet.balance,
        "total_earned": wallet.total_earned,
    }


# === Transfer & Transactions ===

@router.post("/groups/{group_id}/economy/transfer")
async def transfer_coins(
    group_id: int,
    request: TransactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transfer coins to another user (/give, /transfer, /pay)."""
    # Get config
    result = await db.execute(
        select(EconomyConfig).where(EconomyConfig.group_id == group_id)
    )
    config = result.scalar()
    min_transfer = config.min_transfer if config else 1
    max_transfer = config.max_transfer if config else 1000000
    tax_rate = config.tax_rate if config else 0

    if request.amount < min_transfer:
        raise HTTPException(status_code=400, detail=f"Minimum transfer is {min_transfer}")
    if request.amount > max_transfer:
        raise HTTPException(status_code=400, detail=f"Maximum transfer is {max_transfer}")

    # Get sender wallet
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    sender_wallet = result.scalar()

    if not sender_wallet or sender_wallet.balance < request.amount:
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
        recipient_wallet = Wallet(
            user_id=request.to_user_id,
            group_id=group_id,
        )
        db.add(recipient_wallet)
        await db.flush()

    # Calculate tax
    tax_amount = int(request.amount * tax_rate)
    net_amount = request.amount - tax_amount

    # Perform transfer
    sender_wallet.balance -= request.amount
    sender_wallet.total_spent += request.amount
    recipient_wallet.balance += net_amount
    recipient_wallet.total_earned += net_amount

    # Record transaction
    transaction = Transaction(
        from_wallet_id=sender_wallet.id,
        to_wallet_id=recipient_wallet.id,
        amount=net_amount,
        reason=request.reason or "transfer",
        transaction_type="transfer",
    )
    db.add(transaction)

    await db.commit()

    return {
        "success": True,
        "amount": net_amount,
        "tax": tax_amount,
        "new_balance": sender_wallet.balance
    }


@router.get("/groups/{group_id}/economy/transactions", response_model=TransactionHistoryResponse)
async def get_transactions(
    group_id: int,
    page: int = 1,
    page_size: int = 20,
    wallet_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get transaction history (/transactions, /tx)."""
    # Get user's wallet if not specified
    if not wallet_id:
        result = await db.execute(
            select(Wallet).where(
                Wallet.user_id == current_user.id,
                Wallet.group_id == group_id,
            )
        )
        wallet = result.scalar()
        if not wallet:
            return TransactionHistoryResponse(items=[], total=0, page=1, page_size=page_size)
        wallet_id = wallet.id

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Transaction)
        .where(
            (Transaction.from_wallet_id == wallet_id) |
            (Transaction.to_wallet_id == wallet_id)
        )
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    transactions = result.scalars().all()

    total_result = await db.execute(
        select(func.count()).where(
            (Transaction.from_wallet_id == wallet_id) |
            (Transaction.to_wallet_id == wallet_id)
        )
    )
    total = total_result.scalar()

    items = []
    for t in transactions:
        items.append({
            "id": t.id,
            "amount": t.amount,
            "type": t.transaction_type,
            "reason": t.reason,
            "is_incoming": t.to_wallet_id == wallet_id,
            "created_at": t.created_at.isoformat() if t.created_at else "",
        })

    return TransactionHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# === Daily & Work ===

@router.post("/groups/{group_id}/economy/daily", response_model=DailyBonusResponse)
async def claim_daily_bonus(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Claim daily bonus (/daily)."""
    # Get config
    result = await db.execute(
        select(EconomyConfig).where(EconomyConfig.group_id == group_id)
    )
    config = result.scalar()
    daily_bonus = config.daily_bonus if config else 100
    daily_cooldown = config.daily_cooldown if config else 86400

    # Get or create wallet
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet:
        wallet = Wallet(user_id=current_user.id, group_id=group_id, balance=0)
        db.add(wallet)
        await db.flush()

    # Check cooldown
    if wallet.last_daily:
        next_available = wallet.last_daily + timedelta(seconds=daily_cooldown)
        if datetime.utcnow() < next_available:
            raise HTTPException(
                status_code=400,
                detail=f"Daily bonus available at {next_available.isoformat()}"
            )

    # Award bonus
    wallet.balance += daily_bonus
    wallet.total_earned += daily_bonus
    wallet.last_daily = datetime.utcnow()

    # Record transaction
    transaction = Transaction(
        from_wallet_id=wallet.id,
        to_wallet_id=wallet.id,
        amount=daily_bonus,
        reason="daily bonus",
        transaction_type="earned",
    )
    db.add(transaction)
    await db.commit()

    next_available = wallet.last_daily + timedelta(seconds=daily_cooldown)

    return DailyBonusResponse(
        bonus=daily_bonus,
        new_balance=wallet.balance,
        next_available=next_available.isoformat(),
        streak=1,  # Would need streak tracking in wallet
    )


@router.post("/groups/{group_id}/economy/work", response_model=WorkResponse)
async def do_work(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Work to earn coins (/work)."""
    result = await db.execute(
        select(EconomyConfig).where(EconomyConfig.group_id == group_id)
    )
    config = result.scalar()
    work_cooldown = config.work_cooldown if config else 3600

    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet:
        wallet = Wallet(user_id=current_user.id, group_id=group_id)
        db.add(wallet)
        await db.flush()

    if wallet.last_work:
        next_available = wallet.last_work + timedelta(seconds=work_cooldown)
        if datetime.utcnow() < next_available:
            raise HTTPException(
                status_code=400,
                detail=f"Work available at {next_available.isoformat()}"
            )

    # Calculate work earnings (random between 10-50)
    import random
    earned = random.randint(10, 50)

    wallet.balance += earned
    wallet.total_earned += earned
    wallet.last_work = datetime.utcnow()

    transaction = Transaction(
        from_wallet_id=wallet.id,
        to_wallet_id=wallet.id,
        amount=earned,
        reason="work",
        transaction_type="earned",
    )
    db.add(transaction)
    await db.commit()

    next_available = wallet.last_work + timedelta(seconds=work_cooldown)

    return WorkResponse(
        earned=earned,
        new_balance=wallet.balance,
        next_available=next_available.isoformat(),
    )


@router.post("/groups/{group_id}/economy/beg", response_model=WorkResponse)
async def beg_for_coins(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Beg for coins (/beg)."""
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet:
        wallet = Wallet(user_id=current_user.id, group_id=group_id)
        db.add(wallet)
        await db.flush()

    # Random chance to get coins
    import random
    if random.random() < 0.3:  # 30% chance
        earned = random.randint(1, 20)
        wallet.balance += earned
        wallet.total_earned += earned

        transaction = Transaction(
            from_wallet_id=wallet.id,
            to_wallet_id=wallet.id,
            amount=earned,
            reason="begging",
            transaction_type="earned",
        )
        db.add(transaction)
        await db.commit()

        return WorkResponse(
            earned=earned,
            new_balance=wallet.balance,
            next_available=datetime.utcnow().isoformat(),
        )
    else:
        raise HTTPException(status_code=400, detail="Nobody gave you any coins this time")


# === Gambling ===

@router.post("/groups/{group_id}/economy/gamble", response_model=GambleResponse)
async def gamble_coins(
    group_id: int,
    request: GambleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Gamble coins (/gamble, /coinflip)."""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet or wallet.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    import random
    result_choice = random.choice(["heads", "tails"])
    won = request.choice.lower() == result_choice

    if won:
        wallet.balance += request.amount
        wallet.total_earned += request.amount
        message = f"You won! It was {result_choice}"
    else:
        wallet.balance -= request.amount
        wallet.total_spent += request.amount
        message = f"You lost! It was {result_choice}"

    transaction = Transaction(
        from_wallet_id=wallet.id,
        to_wallet_id=wallet.id,
        amount=request.amount,
        reason=f"gamble ({request.choice} vs {result_choice})",
        transaction_type="gamble",
    )
    db.add(transaction)
    await db.commit()

    return GambleResponse(
        won=won,
        amount=request.amount,
        new_balance=wallet.balance,
        result=result_choice,
    )


@router.post("/groups/{group_id}/economy/rob", response_model=RobResponse)
async def rob_user(
    group_id: int,
    request: RobRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rob another user (/rob)."""
    if current_user.id == request.target_user_id:
        raise HTTPException(status_code=400, detail="You can't rob yourself")

    # Get target wallet
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == request.target_user_id,
            Wallet.group_id == group_id,
        )
    )
    target_wallet = result.scalar()

    if not target_wallet or target_wallet.balance < 10:
        raise HTTPException(status_code=400, detail="Target has insufficient balance")

    # Get your wallet
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet:
        wallet = Wallet(user_id=current_user.id, group_id=group_id)
        db.add(wallet)
        await db.flush()

    # Rob chance
    import random
    if random.random() < 0.5:  # 50% chance
        amount = random.randint(10, min(100, target_wallet.balance // 2))
        wallet.balance += amount
        wallet.total_earned += amount
        target_wallet.balance -= amount
        target_wallet.total_spent += amount

        transaction = Transaction(
            from_wallet_id=target_wallet.id,
            to_wallet_id=wallet.id,
            amount=amount,
            reason="robbery",
            transaction_type="transfer",
        )
        db.add(transaction)
        await db.commit()

        return RobResponse(
            success=True,
            amount=amount,
            new_balance=wallet.balance,
            message=f"You successfully stole {amount} coins!"
        )
    else:
        # Failed robbery - small penalty
        penalty = random.randint(5, 25)
        wallet.balance = max(0, wallet.balance - penalty)
        wallet.total_spent += penalty

        await db.commit()

        return RobResponse(
            success=False,
            amount=penalty,
            new_balance=wallet.balance,
            message=f"You were caught! Paid {penalty} coins as a fine."
        )


# === Bank Operations ===

@router.get("/groups/{group_id}/economy/bank", response_model=BankResponse)
async def get_bank_info(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get bank balance (/bank)."""
    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet:
        return BankResponse(balance=0, bank_balance=0, total_assets=0)

    return BankResponse(
        balance=wallet.balance,
        bank_balance=wallet.bank_balance,
        total_assets=wallet.balance + wallet.bank_balance,
    )


@router.post("/groups/{group_id}/economy/deposit")
async def deposit_to_bank(
    group_id: int,
    request: BankOperationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deposit coins to bank (/deposit)."""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet or wallet.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    wallet.balance -= request.amount
    wallet.bank_balance += request.amount

    await db.commit()

    return {
        "success": True,
        "balance": wallet.balance,
        "bank_balance": wallet.bank_balance,
    }


@router.post("/groups/{group_id}/economy/withdraw")
async def withdraw_from_bank(
    group_id: int,
    request: BankOperationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Withdraw coins from bank (/withdraw)."""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet or wallet.bank_balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient bank balance")

    wallet.bank_balance -= request.amount
    wallet.balance += request.amount

    await db.commit()

    return {
        "success": True,
        "balance": wallet.balance,
        "bank_balance": wallet.bank_balance,
    }


@router.post("/groups/{group_id}/economy/loan", response_model=LoanResponse)
async def take_loan(
    group_id: int,
    request: LoanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Take a loan (/loan)."""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    max_loan = 10000  # Max loan amount

    if request.amount > max_loan:
        raise HTTPException(status_code=400, detail=f"Maximum loan is {max_loan}")

    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet:
        wallet = Wallet(user_id=current_user.id, group_id=group_id)
        db.add(wallet)
        await db.flush()

    # Check existing loan
    if wallet.loan_amount > 0:
        raise HTTPException(status_code=400, detail="You already have an outstanding loan")

    # Grant loan
    wallet.bank_balance += request.amount
    wallet.loan_amount = request.amount

    await db.commit()

    # Calculate monthly payment (5% interest)
    total_repayment = int(request.amount * 1.05)
    monthly_payment = total_repayment // 12

    return LoanResponse(
        loan_amount=wallet.loan_amount,
        new_balance=wallet.bank_balance,
        monthly_payment=monthly_payment,
    )


@router.post("/groups/{group_id}/economy/repay")
async def repay_loan(
    group_id: int,
    request: BankOperationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Repay loan (/repay)."""
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet or wallet.loan_amount == 0:
        raise HTTPException(status_code=400, detail="No active loan")

    if wallet.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    wallet.balance -= request.amount
    wallet.loan_amount = max(0, wallet.loan_amount - request.amount)

    await db.commit()

    return {
        "success": True,
        "loan_remaining": wallet.loan_amount,
        "balance": wallet.balance,
    }


# === Leaderboard ===

@router.get("/groups/{group_id}/economy/leaderboard")
async def get_leaderboard(
    group_id: int,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get economy leaderboard (/leaderboard, /lb, /rich)."""
    result = await db.execute(
        select(Wallet, User)
        .join(User, Wallet.user_id == User.id)
        .where(Wallet.group_id == group_id)
        .order_by(Wallet.balance.desc())
        .limit(limit)
    )

    leaderboard = []
    for i, (wallet, user) in enumerate(result.all()):
        leaderboard.append({
            "rank": i + 1,
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": wallet.balance,
            "bank_balance": wallet.bank_balance,
            "total_assets": wallet.balance + wallet.bank_balance,
            "total_earned": wallet.total_earned,
        })

    return leaderboard


# === Shop (Basic) ===

@router.get("/groups/{group_id}/economy/shop")
async def get_shop_items(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get shop items (/shop)."""
    # This would typically come from a database table
    # For now, returning default items
    shop_items = [
        {"id": 1, "name": "Premium Badge", "description": "Show off your status", "price": 500, "emoji": "⭐", "category": "badges"},
        {"id": 2, "name": "Color Name", "description": "Get a colored username", "price": 1000, "emoji": "🌈", "category": "cosmetics"},
        {"id": 3, "name": "Extra Daily", "description": "Get bonus daily coins", "price": 2000, "emoji": "💰", "category": "boosters"},
        {"id": 4, "name": "Custom Emoji", "description": "Use custom emoji in chat", "price": 3000, "emoji": "😎", "category": "cosmetics"},
        {"id": 5, "name": "VIP Access", "description": "Access to VIP commands", "price": 5000, "emoji": "👑", "category": "access"},
    ]
    return shop_items


@router.post("/groups/{group_id}/economy/buy/{item_id}")
async def buy_item(
    group_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Buy item from shop (/buy)."""
    shop_prices = {
        1: 500,
        2: 1000,
        3: 2000,
        4: 3000,
        5: 5000,
    }

    price = shop_prices.get(item_id)
    if not price:
        raise HTTPException(status_code=404, detail="Item not found")

    result = await db.execute(
        select(Wallet).where(
            Wallet.user_id == current_user.id,
            Wallet.group_id == group_id,
        )
    )
    wallet = result.scalar()

    if not wallet or wallet.balance < price:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    wallet.balance -= price
    wallet.total_spent += price

    await db.commit()

    return {
        "success": True,
        "item_id": item_id,
        "new_balance": wallet.balance,
    }


# === Statistics ===

@router.get("/groups/{group_id}/economy/stats", response_model=EconomyStatsResponse)
async def get_economy_stats(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get economy statistics."""
    # Total supply
    total_result = await db.execute(
        select(func.coalesce(func.sum(Wallet.balance), 0)).where(Wallet.group_id == group_id)
    )
    total_supply = total_result.scalar() or 0

    # Total transactions
    tx_result = await db.execute(
        select(func.count(Transaction.id))
    )
    total_transactions = tx_result.scalar() or 0

    # Total wallets
    wallets_result = await db.execute(
        select(func.count(Wallet.id)).where(Wallet.group_id == group_id)
    )
    total_wallets = wallets_result.scalar() or 0

    # Daily volume (transactions in last 24h)
    day_ago = datetime.utcnow() - timedelta(days=1)
    volume_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.created_at >= day_ago)
    )
    daily_volume = volume_result.scalar() or 0

    # Richest user
    result = await db.execute(
        select(Wallet, User)
        .join(User, Wallet.user_id == User.id)
        .where(Wallet.group_id == group_id)
        .order_by(Wallet.balance.desc())
        .limit(1)
    )
    rich = result.first()
    richest_user = None
    if rich:
        wallet, user = rich
        richest_user = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": wallet.balance,
        }

    return EconomyStatsResponse(
        total_supply=total_supply,
        total_transactions=total_transactions,
        total_wallets=total_wallets,
        daily_volume=daily_volume,
        richest_user=richest_user,
    )

