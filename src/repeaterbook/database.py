"""Internal database module for RepeaterBook."""

from __future__ import annotations

__all__: tuple[str, ...] = ("RepeaterBook",)

from functools import cached_property
from typing import TYPE_CHECKING

import attrs
from anyio import Path
from loguru import logger
from sqlmodel import Session, SQLModel, create_engine, select

from repeaterbook.models import (
    Repeater,
)

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable, Sequence

    from sqlalchemy import Engine
    from sqlalchemy.sql._typing import _ColumnExpressionArgument


@attrs.frozen
class RepeaterBook:
    """RepeaterBook API client."""

    working_dir: Path = attrs.Factory(Path)
    database: str = "repeaterbook.db"

    @property
    def database_path(self) -> Path:
        """Database path."""
        return self.working_dir / self.database

    @property
    def database_uri(self) -> str:
        """Database URI."""
        return f"sqlite:///{self.database_path}"

    @cached_property
    def engine(self) -> Engine:
        """Create database engine."""
        return create_engine(self.database_uri)

    def init_db(self) -> None:
        """Initialize database."""
        SQLModel.metadata.create_all(self.engine)

    def populate(self, repeaters: Iterable[Repeater]) -> None:
        """Populate internal database."""
        self.init_db()

        with Session(self.engine) as session:
            for repeater in repeaters:
                session.merge(repeater)
            session.commit()

        logger.info("Populated repeaters.")

    def query(
        self,
        *where: _ColumnExpressionArgument[bool] | bool,
    ) -> Sequence[Repeater]:
        """Query the database."""
        with Session(self.engine) as session:
            statement = select(Repeater).where(*where)
            repeaters = session.exec(statement).all()

        logger.info(f"Found {len(repeaters)} repeaters.")

        return repeaters
