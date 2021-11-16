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

from volley.config import ENV
from volley.connectors.base import Consumer, Producer
from volley.connectors.pg_config import (
    PG_SCHEMA,
    get_eng,
    init_schema,
    metadata_obj,
    publisher,
)
from volley.data_models import QueueMessage
from volley.logging import logger

BATCH_SIZE = 1
RUN_ONCE = False

PROCESS_TIME = Summary("postgres_process_time_seconds", "Time spent interacting with postgres", ["operation"])


@dataclass
class PGConsumer(Consumer):
    host = os.getenv("PG_HOST", "postgres")

    engine: Engine = get_eng()

    def __post_init__(self) -> None:
        self.engine: Engine = get_eng()
        if ENV == "localhost":
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
        """reads a records (message) off a postgres table (queue)
        messages must meet the follow criteria to leave the queue:
            1) not expired and contain optimizer solution
            2) expired and contain a fallback solution
        reading a record is done in a delete transaction. the transaction
        is not committed unless the message is successfully processed and
        published to the next queue.

        the queue should be processed FIFO by (by expiration)
        """
        records: List[RowMapping] = []
        while not records:
            now = str(datetime.utcnow())
            sql = f"""
                BEGIN;
                DELETE FROM
                    {PG_SCHEMA}.{queue_name}
                USING (
                    SELECT *
                    FROM {PG_SCHEMA}.{queue_name}
                    WHERE (timeout < '{now}' and fallback_id IS NOT NULL) OR (optimizer_id IS NOT NULL)
                    ORDER BY timeout ASC
                    LIMIT {BATCH_SIZE}
                    FOR UPDATE SKIP LOCKED
                ) q
                WHERE q.engine_event_id = {PG_SCHEMA}.{queue_name}.engine_event_id
                RETURNING {PG_SCHEMA}.{queue_name}.*;
            """
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
    host = os.getenv("PG_HOST", "postgres")

    def __post_init__(self) -> None:
        # TODO: are there implications of "if not exists"?
        self.engine: Engine = get_eng()
        if ENV == "localhost":
            init_schema(self.engine)
        metadata_obj.create_all(self.engine)

    def produce(self, queue_name: str, message: QueueMessage) -> bool:
        return_status = True
        rows_updated = 0
        if isinstance(message.message, dict):
            m = message.message
        else:
            m = message.message.dict()
        # remove nulls
        m = {k: v for k, v in m.items() if v is not None}
        event_type = m.pop("event_type")
        bundle_request_id = m["bundle_request_id"]
        engine_event_id = m["engine_event_id"]
        logger.info(m)
        if event_type == "triage":
            insert_stmt = insert(publisher).values(**m)
            with self.engine.begin() as c:
                _start = time.time()
                rows_updated = c.execute(insert_stmt).rowcount
                _duration = time.time() - _start
                PROCESS_TIME.labels("insert").observe(_duration)
        elif event_type in ["fallback", "optimizer"]:
            update_stmt = update(publisher).where(publisher.c.engine_event_id == engine_event_id).values(**m)
            with self.engine.begin() as c:
                _start = time.time()
                rows_updated = c.execute(update_stmt).rowcount
                _duration = time.time() - _start
                PROCESS_TIME.labels("update").observe(_duration)
        else:
            return_status = False
            logger.error(f"unrecognized {event_type=}")
        if rows_updated != 1:
            # there will be no rows updated when:
            # 1) triage had a failure and never inserted a record
            # 2) this is a optimizer event, and timeout expired resulting in the message being published/deleted
            # 3) this is a fallback event, fallback was slow and optimizer published resulting in message being deleted
            logger.warning(f"no records updated {bundle_request_id=} - {event_type=} - {rows_updated=}")
        return return_status

    def shutdown(self) -> None:
        pass
