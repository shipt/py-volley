import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List

from prometheus_client import Summary
from sqlalchemy import text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.row import RowMapping
from sqlalchemy.orm import Session

from engine.connectors.base import Consumer, Producer
from engine.connectors.pg_config import (
    PG_SCHEMA,
    get_eng,
    init_schema,
    metadata_obj,
    publisher,
)
from engine.data_models import QueueMessage
from engine.logging import logger

BATCH_SIZE = 1
RUN_ONCE = False

PROCESS_TIME = Summary("postgres_process_time_seconds", "Time spent interacting with postgres", ["operation"])


@dataclass
class PGConsumer(Consumer):
    engine: Engine = get_eng()

    def __post_init__(self) -> None:
        self.engine: Engine = get_eng()
        if os.getenv("APP_ENV") == "localhost":
            init_schema(self.engine)

        # close make sure table is created
        metadata_obj.create_all(self.engine)
        self.session = Session(self.engine)
        # close the session and transaction
        self.session.close()

    def consume(
        self,
        queue_name: str = None,
        timeout: float = 60,
        poll_interval: float = 2,
    ) -> QueueMessage:
        now = str(datetime.utcnow())
        sql = f"""
            BEGIN;
            DELETE FROM
                {PG_SCHEMA}.{queue_name}
            USING (
                SELECT *
                FROM {PG_SCHEMA}.{queue_name}
                WHERE (timeout < '{now}' OR optimizer_id IS NOT NULL)
                LIMIT {BATCH_SIZE}
                FOR UPDATE SKIP LOCKED
            ) q
            WHERE q.engine_event_id = {PG_SCHEMA}.{queue_name}.engine_event_id
            RETURNING {PG_SCHEMA}.{queue_name}.*;
        """

        records: List[RowMapping] = []
        while not records:
            _start = time.time()
            records = [r._mapping for r in self.session.execute(text(sql))]
            _duration = time.time() - _start
            PROCESS_TIME.labels("read").observe(_duration)
            if not any(records):
                logger.info(f"No records - waiting {poll_interval}")
                self.session.execute(text("ROLLBACK;"))
                time.sleep(poll_interval)

            if RUN_ONCE:
                break

        return QueueMessage(message_id="None", message={"results": records})

    def delete_message(self, queue_name: str, message_id: str) -> bool:  # type: ignore
        # if all succeeds, commit the transaction
        _start = time.time()
        self.session.execute(text("COMMIT;"))
        _duration = time.time() - _start
        PROCESS_TIME.labels("delete").observe(_duration)
        return True

    def on_fail(self) -> None:
        # rollback the DELETE transaction
        self.session.execute(text("ROLLBACK;"))

    def shutdown(self) -> None:
        self.session.close()


@dataclass
class PGProducer(Producer):
    def __post_init__(self) -> None:
        # TODO: are there implications of "if not exists"?
        self.engine: Engine = get_eng()
        if os.getenv("APP_ENV") == "localhost":
            init_schema(self.engine)
        metadata_obj.create_all(self.engine)

    def produce(self, queue_name: str, message: QueueMessage) -> bool:
        if isinstance(message.message, dict):
            m = message.message
        else:
            m = message.message.dict()
        # remove nulls
        m = {k: v for k, v in m.items() if v is not None}
        event_type = m.pop("event_type")
        engine_event_id = m["engine_event_id"]
        logger.info(m)
        if event_type == "triage":
            insert_stmt = insert(publisher).values(**m)
            with self.engine.begin() as c:
                _start = time.time()
                c.execute(insert_stmt)
                _duration = time.time() - _start
                PROCESS_TIME.labels("insert").observe(_duration)
        elif event_type in ["fallback", "optimizer"]:
            update_stmt = update(publisher).where(publisher.c.engine_event_id == engine_event_id).values(**m)
            with self.engine.begin() as c:
                _start = time.time()
                c.execute(update_stmt)
                _duration = time.time() - _start
                PROCESS_TIME.labels("update").observe(_duration)
        else:
            logger.error(f"unrecognized {event_type=}")
        return True

    def shutdown(self) -> None:
        pass
