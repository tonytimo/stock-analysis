"""
This module contains the database manager functions.
"""

import datetime
from sqlalchemy import create_engine, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column


DATABASE_URL = "sqlite:////data/stock_data.db"
engine = create_engine(DATABASE_URL, echo=False)

# SessionLocal is a factory that creates Session objects
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class StockPrice(Base):
    """
    A class to represent the stock_prices table.
    """

    __tablename__ = "stock_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(10))
    price: Mapped[float]
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )


def init_db():
    """Create the table if it doesn't exist."""
    Base.metadata.create_all(bind=engine)


def insert_stock_price(symbol: str, price: float, ts=None) -> None:
    """
    Insert a single stock price record into the database.
    """
    if ts is None:
        ts = datetime.datetime.utcnow()

    # Use a context manager for the session
    with SessionLocal() as db:
        record = StockPrice(symbol=symbol, price=price, timestamp=ts)
        db.add(record)
        db.commit()


def get_recent_stock_prices(limit: int = 100):
    """
    Retrieve the most recent records (sorted by timestamp desc).
    Return them as a list of StockPrice objects.
    """
    with SessionLocal() as db:
        results = (
            db.query(StockPrice)
            .order_by(StockPrice.timestamp.desc())
            .limit(limit)
            .all()
        )

        return results
