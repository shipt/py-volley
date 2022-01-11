from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Float, MetaData, String, Table, create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session
from sqlalchemy.sql.sqltypes import DateTime

from volley.connectors.base import BaseConsumer, BaseProducer
from volley.data_models import QueueMessage
from volley.logging import logger


def get_eng() -> Engine:
    connection_str = "{}://{}:{}@{}:{}/{}".format("postgresql", "postgres", "password", "postgres", 5432, "postgres")
    return create_engine(connection_str, connect_args={"connect_timeout": 2}, pool_pre_ping=True)


metadata_obj = MetaData()


queue_table = Table(
    "my_long_table_name",
    metadata_obj,
    Column("request_id", String(40), nullable=False),
    Column("max_plus", Float),
    Column("message_sent_at", DateTime),
)


@dataclass
class MyPGConsumer(BaseConsumer):
    def __post_init__(self) -> None:
        self.engine: Engine = get_eng()
        metadata_obj.create_all(self.engine)
        self.session = Session(self.engine)

    def consume(
        self,
        queue_name: str = None,
        timeout: float = 60,
        poll_interval: float = 2,
    ) -> QueueMessage:
        """returns a random value"""
        sql = f"""
            BEGIN;
            WITH cte AS
                (
                    SELECT *
                    FROM '{queue_name}'
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
            DELETE from '{queue_name}'
            WHERE request_id = (select request_id from cte)
            RETURNING *;
        """

        records = [r._mapping for r in self.session.execute(text(sql))]

        return QueueMessage(message_context="None", message={"results": records})

    def on_success(self, queue_name: str, message_context: str) -> bool:
        self.session.execute(text("COMMIT;"))
        return True

    def on_fail(self) -> None:
        self.session.execute(text("ROLLBACK;"))

    def shutdown(self) -> None:
        self.session.close()


@dataclass
class MyPGProducer(BaseProducer):
    def __post_init__(self) -> None:
        self.engine: Engine = get_eng()
        metadata_obj.create_all(self.engine)
        self.session = Session(self.engine)

    def produce(self, queue_name: str, message: dict[str, Any], **kwargs: Any) -> bool:
        logger.info(f"produced message to: {queue_name=} - message={message}")
        vals = {
            "message_sent_at": datetime.now(),
            "request_id": message["request_id"],
            "max_plus": message["max_plus"],
        }
        insert_stmt = insert(queue_table).values(**vals)
        with self.engine.begin() as c:
            c.execute(insert_stmt).rowcount
        return True

    def shutdown(self) -> None:
        pass
