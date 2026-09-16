"""Product ratings. ALWAYS ours, regardless of data_mode. product_ref = id/name from either system."""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (CheckConstraint("stars >= 1 AND stars <= 5", name="ratings_stars_range"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    product_ref: Mapped[str] = mapped_column(String, nullable=False)
    customer_phone: Mapped[str] = mapped_column(String, nullable=False)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
