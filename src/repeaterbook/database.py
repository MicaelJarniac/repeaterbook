"""Internal database module for the RepeaterBook Python Client."""

from __future__ import annotations

__all__: tuple[str, ...] = ("SCHEMA_VERSION_KEY", "RepeaterBook", "schema_fingerprint")

import hashlib
import os
import sqlite3
from contextlib import closing
from functools import cached_property
from typing import TYPE_CHECKING, Self

import attrs
from anyio import Path
from loguru import logger
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine, delete, select

from repeaterbook.models import (
    Repeater,
)

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable, Sequence
    from types import TracebackType

    from sqlalchemy import Engine
    from sqlalchemy.sql._typing import _ColumnExpressionArgument

# Where the fingerprint lives inside the database file. A dedicated one-row
# table rather than SQLite's `PRAGMA user_version`, which holds a 32-bit int
# and is the kind of slot another tool might also decide to use.
SCHEMA_VERSION_KEY = "repeaterbook_schema"
_SCHEMA_TABLE = "repeaterbook_schema_version"


def schema_fingerprint() -> str:
    """Return a digest of the ORM schema as currently defined in code.

    Derived from the model metadata rather than hand-maintained, so it moves
    on its own whenever a column is added, removed, renamed, retyped, or has
    its nullability or primary-key membership changed. A contributor changing
    the model gets the stale-database wipe for free, without having to know
    this mechanism exists -- which is the point, because the failure mode of a
    forgotten manual bump is a silent misread rather than a loud error.

    Deliberately over-sensitive: an index-only change also moves the digest,
    costing a re-download that was not strictly required. That is the right
    trade when the alternative is serving wrong data from a stale file.
    """
    parts: list[str] = []
    for table in SQLModel.metadata.sorted_tables:
        parts.append(table.name)
        parts.extend(
            f"{column.name}:{column.type!r}:{column.nullable}:{column.primary_key}"
            for column in table.columns
        )
        parts.extend(sorted(index.name or "" for index in table.indexes))
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


@attrs.frozen
class RepeaterBook:
    """Local database for repeater data from the RepeaterBook.com API.

    This file is a **cache**, not durable storage. It holds nothing that
    cannot be re-downloaded from RepeaterBook, so when the schema in code no
    longer matches the schema the file was written with, the file is discarded
    and rebuilt rather than migrated. Keep your own data somewhere else.

    The underlying engine and its connection pool are created lazily on first
    use and live until `close()` is called, so use the instance as a context
    manager (or call `close()` yourself) to release the SQLite handle when you
    are done. Closing is optional: an instance that is never closed still
    works, and its connections are finalized when it is garbage collected.
    """

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
        """Create database engine, discarding the file if its schema is stale.

        The check lives here rather than in `init_db` because reading from a
        stale file has to be caught too, and `query` never calls `init_db`.
        This is the one path every caller goes through.
        """
        self._discard_if_stale()
        engine = create_engine(self.database_uri)
        # Always leave a usable, current-schema database behind. Chiefly so a
        # caller that only queries sees "no repeaters yet" instead of a
        # missing-table error from a file discarded under them, but it also
        # makes a never-populated working directory behave the same way
        # rather than raising.
        SQLModel.metadata.create_all(engine)
        self._record_fingerprint(engine)
        return engine

    def close(self) -> None:
        """Dispose of the engine and release its pooled SQLite connections.

        The instance stays usable: the next access to `engine` (directly or
        via `populate`, `query` or `truncate`) builds a fresh one, re-running
        the staleness check. Calling this on an instance whose engine was
        never built, or that is already closed, is a no-op.

        Any `Session` you built against the old `engine` yourself is not
        tracked here; close those first.
        """
        # `attrs.frozen` makes the class slotted, so the cached engine lives in
        # a slot rather than `__dict__`, and `del self.engine` is refused by
        # the frozen `__delattr__`. Going through `object` bypasses both the
        # freeze and attrs' lazy-building `__getattr__`: an empty slot raises
        # rather than constructing an engine only to throw it away.
        try:
            engine: Engine = object.__getattribute__(self, "engine")
        except AttributeError:
            return
        object.__delattr__(self, "engine")
        engine.dispose()
        logger.debug(f"Closed database at {self.database_path}.")

    def __enter__(self) -> Self:
        """Enter the runtime context; the engine is still built lazily."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the runtime context, releasing the database handle."""
        self.close()

    def _discard_if_stale(self) -> None:
        """Delete the database file if it predates the current schema.

        A no-op when the file is absent or already current. An unreadable or
        corrupt file counts as stale: it cannot be trusted either way, and the
        contents are re-downloadable.
        """
        path = self.database_path
        if not os.path.exists(path):  # noqa: PTH110 -- anyio.Path, sync context
            return

        expected = schema_fingerprint()
        found = self._stored_fingerprint()
        if found == expected:
            return

        reason = "written by an older schema" if found else "missing its schema marker"
        logger.warning(
            f"Discarding cached database at {path}: {reason} "
            f"(found {found or 'nothing'}, expected {expected}). "
            "It holds only re-downloadable data; populate it again to refill."
        )
        os.unlink(path)  # noqa: PTH108 -- anyio.Path, sync context

    def _stored_fingerprint(self) -> str | None:
        """Read the fingerprint recorded in the database file, if any.

        Uses sqlite3 directly rather than an Engine: this runs *before* the
        cached engine exists, and building a throwaway one here would leave a
        second connection pool behind on every instance.
        """
        # `closing`, not the connection's own context manager: that one
        # commits on exit but leaves the handle open.
        try:
            with closing(sqlite3.connect(os.fspath(self.database_path))) as connection:
                row = connection.execute(
                    f"SELECT fingerprint FROM {_SCHEMA_TABLE} WHERE key = ?",  # noqa: S608
                    (SCHEMA_VERSION_KEY,),
                ).fetchone()
        except sqlite3.DatabaseError:
            # No marker table, or the file is not a readable database. Either
            # way it predates this mechanism or is unusable, so treat it as
            # stale rather than guessing.
            return None
        else:
            return str(row[0]) if row else None

    def init_db(self) -> None:
        """Initialize database, recording the schema it was created with.

        Kept as public API, but building the engine already does this, so it
        is a no-op on an engine that has been touched.
        """
        SQLModel.metadata.create_all(self.engine)
        self._record_fingerprint(self.engine)

    def _record_fingerprint(self, engine: Engine) -> None:
        """Stamp the current schema fingerprint into the database file.

        Takes the engine explicitly because one caller is `engine` itself,
        mid-construction, where the cached property is not yet available.
        """
        with engine.begin() as connection:
            connection.execute(
                text(
                    f"CREATE TABLE IF NOT EXISTS {_SCHEMA_TABLE} "
                    "(key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL)"
                )
            )
            connection.execute(
                text(
                    f"INSERT INTO {_SCHEMA_TABLE} (key, fingerprint)"  # noqa: S608
                    " VALUES (:key, :fingerprint)"
                    " ON CONFLICT(key) DO UPDATE SET fingerprint = :fingerprint"
                ),
                {"key": SCHEMA_VERSION_KEY, "fingerprint": schema_fingerprint()},
            )

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

    def truncate(self) -> int:
        """Delete every repeater, leaving the file and its schema marker in place.

        This empties the data without making the file look stale: the next open
        finds a current, empty database rather than one to discard. It does
        not touch the API response cache, which `RepeaterBookAPI` owns; a
        `populate` shortly after a truncate may therefore be served from that
        cache rather than the network.

        Returns:
            The number of repeaters removed.
        """
        with Session(self.engine) as session:
            removed = session.exec(delete(Repeater)).rowcount
            session.commit()

        logger.info(f"Truncated {removed} repeaters.")
        return removed
