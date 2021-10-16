from sqlalchemy import Column, DateTime, MetaData, String, Table, create_engine, text
from sqlalchemy.engine.base import Engine
from sqlalchemy.sql.sqltypes import JSON

PG_DATABASE = "postgres"
PG_SCHEMA = "bundle_engine"
PG_USER = "postgres"
PG_PASS = "password"
PG_HOST = "postgres"
PG_PORT = 5432


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


collector = Table(
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


def get_eng(timeout: int = 2) -> Engine:
    connection_str = "{}://{}:{}@{}:{}/{}".format(
        "postgresql", PG_USER, PG_PASS, PG_HOST, PG_PORT, PG_DATABASE
    )
    return create_engine(
        connection_str, connect_args={"connect_timeout": timeout}, pool_pre_ping=True
    )
