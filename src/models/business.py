"""A tenant (small business) using the WhatsApp agent."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    whatsapp_phone_number_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    # 'hosted' -> use our own products/orders tables. 'api' -> call client's own API.
    data_mode: Mapped[str] = mapped_column(String, nullable=False, default="hosted")
    client_api_base_url: Mapped[str | None] = mapped_column(String, nullable=True)
    client_api_key: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    products: Mapped[list["Product"]] = relationship(back_populates="business")
    orders: Mapped[list["Order"]] = relationship(back_populates="business")
