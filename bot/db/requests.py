from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    BidStatus,
    InstallerProfile,
    Order,
    OrderBid,
    OrderStatus,
    User,
    UserRole,
)


async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    full_name: str | None,
    role: UserRole = UserRole.client,
) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user:
        if full_name and user.full_name != full_name:
            user.full_name = full_name
        return user
    user = User(telegram_id=telegram_id, full_name=full_name, role=role)
    session.add(user)
    await session.flush()
    return user


async def accept_terms(session: AsyncSession, telegram_id: int) -> None:
    user = await get_or_create_user(
        session, telegram_id=telegram_id, full_name=None, role=UserRole.client
    )
    user.accepted_terms = True
    await session.flush()


async def create_order(
    session: AsyncSession,
    *,
    client: User,
    category: str,
    object_type: str,
    points_count: str,
    require_ups: bool,
    photos: list[str],
    estimated_price_min: int,
    estimated_price_max: int,
) -> Order:
    order = Order(
        client_id=client.id,
        category=category,
        object_type=object_type,
        points_count=points_count,
        require_ups=require_ups,
        photos=photos,
        estimated_price_min=estimated_price_min,
        estimated_price_max=estimated_price_max,
        status=OrderStatus.draft,
    )
    session.add(order)
    await session.flush()
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    return await session.get(Order, order_id)


async def publish_order(session: AsyncSession, order_id: int) -> Order | None:
    order = await get_order(session, order_id)
    if order:
        order.status = OrderStatus.published
        await session.flush()
    return order


async def create_bid(
    session: AsyncSession,
    *,
    order_id: int,
    installer: User,
    price_offer: int,
    comment: str,
) -> OrderBid:
    bid = OrderBid(
        order_id=order_id,
        installer_id=installer.id,
        price_offer=price_offer,
        comment=comment,
        status=BidStatus.pending,
    )
    session.add(bid)
    await session.flush()
    return bid


async def accept_bid(session: AsyncSession, bid_id: int) -> OrderBid | None:
    bid = await session.get(OrderBid, bid_id)
    if not bid:
        return None
    bid.status = BidStatus.accepted
    order = await session.get(Order, bid.order_id)
    if order:
        order.status = OrderStatus.in_progress
        order.selected_installer_id = bid.installer_id
    await session.flush()
    return bid


async def upsert_installer_profile(
    session: AsyncSession,
    *,
    user: User,
    fop_code: str | None,
    test_score: int,
    portfolio_photos: list[str],
) -> InstallerProfile:
    profile = await session.scalar(
        select(InstallerProfile).where(InstallerProfile.user_id == user.id)
    )
    if not profile:
        profile = InstallerProfile(user_id=user.id)
        session.add(profile)
    profile.fop_code = fop_code
    profile.test_score = test_score
    profile.portfolio_photos = portfolio_photos
    profile.is_verified = False
    user.role = UserRole.installer
    await session.flush()
    return profile


async def set_installer_verified(
    session: AsyncSession, installer_user_id: int, is_verified: bool
) -> InstallerProfile | None:
    profile = await session.scalar(
        select(InstallerProfile).where(InstallerProfile.user_id == installer_user_id)
    )
    if not profile:
        return None
    profile.is_verified = is_verified
    profile.verified_at = datetime.now(timezone.utc) if is_verified else None
    await session.flush()
    return profile


async def delete_user_personal_data(session: AsyncSession, telegram_id: int) -> None:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if not user:
        return
    user.full_name = None
    user.phone = None
    user.accepted_terms = False
    await session.execute(delete(OrderBid).where(OrderBid.installer_id == user.id))
    await session.flush()


async def cleanup_old_portfolio_photos(session: AsyncSession, days: int) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    profiles = (
        await session.scalars(
            select(InstallerProfile).where(
                InstallerProfile.verified_at.is_not(None),
                InstallerProfile.verified_at < cutoff,
            )
        )
    ).all()
    for profile in profiles:
        profile.portfolio_photos = []
    await session.flush()
    return len(profiles)
