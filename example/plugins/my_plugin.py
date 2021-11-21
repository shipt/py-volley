from dataclasses import dataclass

from sqlalchemy import Column, Float, MetaData, String, Table, create_engine, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session

from volley.connectors.base import Consumer, Producer
from volley.data_models import QueueMessage
from volley.logging import logger


def get_eng() -> Engine:
    connection_str = "{}://{}:{}@{}:{}/{}".format("postgresql", "postgres", "password", "postgres", 5432, "postgres")
    return create_engine(connection_str, connect_args={"connect_timeout": 2}, pool_pre_ping=True)


metadata_obj = MetaData()


queue_table = Table(
    "my_queue_table",
    metadata_obj,
    Column("request_id", String(40), nullable=False),
    Column("max_plus_1", Float),
)


@dataclass
class MyPGConsumer(Consumer):
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
        sql = """
            BEGIN;
            DELETE FROM my_queue_table
            USING (
                SELECT *
                FROM my_queue_table
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            ) q
            WHERE q.request_id = my_queue_table.request_id
            RETURNING my_queue_table.*;
        """
        records = [r._mapping for r in self.session.execute(text(sql))]

        return QueueMessage(message_id="None", message={"results": records})

    def delete_message(self, queue_name: str, message_id: str) -> bool:  # type: ignore
        self.session.execute(text("COMMIT;"))
        return True

    def on_fail(self) -> None:
        self.session.execute(text("ROLLBACK;"))

    def shutdown(self) -> None:
        self.session.close()


@dataclass
class MyPGProducer(Producer):
    def __post_init__(self) -> None:
        self.engine: Engine = get_eng()
        metadata_obj.create_all(self.engine)
        self.session = Session(self.engine)

    def produce(self, queue_name: str, message: bytes) -> bool:
        logger.info(f"produced message to: {queue_name=} - message={message.message}")
        vals = {
            "request_id": message.message["request_id"],  # type: ignore
            "max_plus_1": message.message["max_plus_1"],  # type: ignore
        }
        insert_stmt = insert(queue_table).values(**vals)
        with self.engine.begin() as c:
            c.execute(insert_stmt).rowcount
        return True

    def shutdown(self) -> None:
        pass
