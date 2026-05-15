"""
persistence.py — SQLite / SQLAlchemy persistence layer.

Stores uploaded CSVs as blobs so they survive container restarts.
Schema
------
datasets (id, filename, upload_date, row_count, raw_csv TEXT)

DB path resolution order (first writable wins):
  1. DB_PATH env var  (set explicitly — Docker / local)
  2. <app_root>/database/storage.db  (relative to this file)
  3. /tmp/storage.db  (Streamlit Cloud fallback — session-scoped)
"""

import io
import os
from datetime import datetime

import pandas as pd
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# ──────────────────────────────────────────────────────────────────
# Resilient DB path — works on Docker, local dev, and Streamlit Cloud
# ──────────────────────────────────────────────────────────────────

def _resolve_db_path() -> str:
    """
    Return the first writable SQLite path from the candidate list.
    Creates the parent directory automatically when possible.
    """
    candidates = [
        # 1. Explicit env var (Docker / local)
        os.environ.get("DB_PATH"),
        # 2. Sibling `database/` dir relative to this file (local dev)
        os.path.join(os.path.dirname(__file__), "..", "database", "storage.db"),
        # 3. /tmp — always writable (Streamlit Cloud)
        "/tmp/storage.db",
    ]

    for path in candidates:
        if not path:
            continue
        path = os.path.abspath(path)
        parent = os.path.dirname(path)
        try:
            os.makedirs(parent, exist_ok=True)
            # Probe write access
            probe = os.path.join(parent, ".write_probe")
            with open(probe, "w") as f:
                f.write("ok")
            os.remove(probe)
            return path
        except OSError:
            continue

    # Should never reach here, but be safe
    return "/tmp/storage.db"


DB_PATH = _resolve_db_path()
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    upload_date = Column(String(50), nullable=False)
    row_count = Column(Integer, nullable=False)
    raw_csv = Column(Text, nullable=False)


Base.metadata.create_all(engine)


# ──────────────────────────────────────────────────────────────────
# Public helpers
# ──────────────────────────────────────────────────────────────────

def save_dataset(filename: str, df: pd.DataFrame) -> int:
    """Serialise *df* and persist it; returns the new row id."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    raw = buf.getvalue()

    with SessionLocal() as session:
        ds = Dataset(
            filename=filename,
            upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            row_count=len(df),
            raw_csv=raw,
        )
        session.add(ds)
        session.commit()
        session.refresh(ds)
        return ds.id


def list_datasets() -> list[dict]:
    """Return lightweight metadata for all stored datasets."""
    with SessionLocal() as session:
        rows = session.query(Dataset).order_by(Dataset.upload_date.desc()).all()
        return [
            {
                "id": r.id,
                "filename": r.filename,
                "upload_date": r.upload_date,
                "row_count": r.row_count,
            }
            for r in rows
        ]


def load_dataset(dataset_id: int) -> pd.DataFrame:
    """Deserialise and return the DataFrame for *dataset_id*."""
    with SessionLocal() as session:
        ds = session.get(Dataset, dataset_id)
        if ds is None:
            raise ValueError(f"Dataset id={dataset_id} not found.")
        return pd.read_csv(io.StringIO(ds.raw_csv))


def delete_dataset(dataset_id: int) -> None:
    """Remove a dataset from the store."""
    with SessionLocal() as session:
        ds = session.get(Dataset, dataset_id)
        if ds:
            session.delete(ds)
            session.commit()
