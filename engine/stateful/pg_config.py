import os

from sqlalchemy import Column, DateTime, MetaData, String, Table, create_engine, text
from sqlalchemy.engine.base import Engine
from sqlalchemy.sql.sqltypes import JSON

PG_SCHEMA = "ml_bundle_engine"

metadata_obj = MetaData(schema=PG_SCHEMA)


def init_schema(engine: Engine) -> None:
    with engine.begin() as con:
        con.execute(
            text(
                f"""
            CREATE SCHEMA IF NOT EXISTS {PG_SCHEMA};
        """
            )
        )


publisher = Table(
    "publisher",
    metadata_obj,
    # triage inserts
    Column("engine_event_id", String(40), unique=True, nullable=False),
    Column("bundle_event_id", String(40), nullable=False),
    Column("store_id", String(40), nullable=False),
    Column("timeout", DateTime, nullable=False),
    # fallback updates
    Column("fallback_id", String(40)),
    Column("fallback_results", JSON),
    Column("fallback_finish", DateTime),
    # optimizer updates
    Column("optimizer_id", String(40)),
    Column("optimizer_results", JSON),
    Column("optimizer_finish", DateTime),
)


def get_eng() -> Engine:
    if not (connection_str := os.getenv("CLOUDSQL_DATABASE_URL")):
        # CLOUDSQL_DATABASE_URL is the configVar in kubedashian
        connection_str = "{}://{}:{}@{}:{}/{}".format(
            "postgresql", "postgres", "password", "postgres", 5432, "postgres"
        )
    return create_engine(connection_str)
