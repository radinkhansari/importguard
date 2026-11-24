from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB


class Base(DeclarativeBase):
    pass


class ImportBatch(Base):
    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(30),
        server_default="pending_review",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class ImportRecord(Base):
    __tablename__ = "import_records"
    __table_args__ = (
        UniqueConstraint("import_id", "record_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    import_id: Mapped[int] = mapped_column(ForeignKey("imports.id"))
    record_number: Mapped[int] = mapped_column()
    data: Mapped[dict] = mapped_column(JSONB)
    errors: Mapped[list] = mapped_column(JSONB, default=list)