import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    Numeric,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base


class UserRole(str, enum.Enum):
    client = "client"
    installer = "installer"
    admin = "admin"


class OrderStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    in_progress = "in_progress"
    completed = "completed"
    canceled = "canceled"


class BidStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.client)
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(255))
    accepted_terms: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    installer_profile: Mapped[Optional["InstallerProfile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(
        foreign_keys="Order.client_id", back_populates="client"
    )
    bids: Mapped[list["OrderBid"]] = relationship(back_populates="installer")


class InstallerProfile(Base):
    __tablename__ = "installer_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    fop_code: Mapped[str | None] = mapped_column(String(64))
    test_score: Mapped[int | None] = mapped_column(Integer)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    portfolio_photos: Mapped[list[str]] = mapped_column(JSONB, default=list)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="installer_profile")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(32))
    object_type: Mapped[str] = mapped_column(String(128))
    points_count: Mapped[str] = mapped_column(String(64))
    require_ups: Mapped[bool] = mapped_column(Boolean, default=False)
    photos: Mapped[list[str]] = mapped_column(JSONB, default=list)
    estimated_price_min: Mapped[int | None] = mapped_column(Integer)
    estimated_price_max: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.draft
    )
    selected_installer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    client: Mapped["User"] = relationship(foreign_keys=[client_id], back_populates="orders")
    selected_installer: Mapped[Optional["User"]] = relationship(
        foreign_keys=[selected_installer_id]
    )
    bids: Mapped[list["OrderBid"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderBid(Base):
    __tablename__ = "order_bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    installer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    price_offer: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[BidStatus] = mapped_column(Enum(BidStatus), default=BidStatus.pending)

    order: Mapped["Order"] = relationship(back_populates="bids")
    installer: Mapped["User"] = relationship(back_populates="bids")


class WebOrder(Base):
    __tablename__ = "web_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer: Mapped[dict] = mapped_column(JSONB, default=dict)
    delivery: Mapped[dict] = mapped_column(JSONB, default=dict)
    items: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(32), default="new", index=True)
    manager_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    event: Mapped[str] = mapped_column(String(64), index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), index=True)
    page: Mapped[str | None] = mapped_column(String(255))
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class PriceOverride(Base):
    __tablename__ = "price_overrides"

    product_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    price_uah: Mapped[float] = mapped_column(Numeric(12, 2))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
