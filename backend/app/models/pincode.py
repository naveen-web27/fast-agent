"""ORM model for India Post's PIN code directory (one row per post-office area)."""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PincodeArea(Base):
    __tablename__ = "pincode_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pincode: Mapped[str] = mapped_column(String, nullable=False)
    area: Mapped[str] = mapped_column(String, nullable=False)
    taluk: Mapped[str] = mapped_column(String, nullable=False, default="")
    district: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
