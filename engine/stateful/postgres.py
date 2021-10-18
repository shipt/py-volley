import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List

from sqlalchemy import text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.row import RowMapping
from sqlalchemy.orm import Session

from core.logging import logger
from engine.consumer import Consumer
from engine.data_models import BundleMessage
from engine.producer import Producer
from engine.stateful.pg_config import (
    PG_SCHEMA,
    get_eng,
    init_schema,
    metadata_obj,
    publisher,
)


@dataclass
class PGConsumer(Consumer):
    engine: Engine = get_eng()

    def __post_init__(self) -> None:
        self.engine: Engine = get_eng()
        if os.getenv("APP_ENV") == "localhost":
            init_schema(self.engine)
        metadata_obj.create_all(self.engine)
        self.session = Session(self.engine)

    def consume(
        self, queue_name: str = None, timeout: float = 60, poll_interval: float = 2
    ) -> BundleMessage:
        now = str(datetime.now())
        BATCH_SIZE = 1
        sql = f"""
            BEGIN;
            DELETE FROM
                {PG_SCHEMA}.{queue_name}
            USING (
                SELECT *
                FROM {PG_SCHEMA}.{queue_name}
                WHERE (timeout >= '{now}' OR optimizer_id IS NOT NULL)
                LIMIT {BATCH_SIZE}
                FOR UPDATE SKIP LOCKED
            ) q
            WHERE q.engine_event_id = {PG_SCHEMA}.{queue_name}.engine_event_idRETURNING {PG_SCHEMA}.{queue_name}.*;
        """

        records: List[RowMapping] = []
        while not records:
            records = [r._mapping for r in self.session.execute(text(sql))]
            if not records:
                logger.info(f"No records - waiting {poll_interval}")
                time.sleep(poll_interval)

        # conn = self.engine.connect()
        # query = delete(publisher)\
        #         .with_for_update(skip_locked=False)\
        #         .filter(
        #             or_(publisher.c.timeout >= now, publisher.c.optimizer_id != None)
        #         )
        # session.execute(query)
        # records = [row._mapping for row in conn.execute(query)]
        # conn.close()
        return BundleMessage(message_id="None", params={}, message={"results": records})

    def delete_message(self, queue_name: str, message_id: str) -> bool:  # type: ignore
        # if all succeeds, commit the transaction
        self.session.commit()
        self.session.close()
        return True

    def on_fail(self) -> None:
        self.session.close()


@dataclass
class PGProducer(Producer):
    def __post_init__(self) -> None:
        # TODO: are there implications of "if not exists"?
        self.engine: Engine = get_eng()
        if os.getenv("APP_ENV") == "localhost":
            init_schema(self.engine)
        metadata_obj.create_all(self.engine)

    def produce(self, queue_name: str, message: BundleMessage) -> bool:
        m = message.message
        event_type = m.pop("event_type")
        engine_event_id = m["engine_event_id"]
        logger.info(m)
        if event_type == "triage":
            insert_stmt = insert(publisher).values(**m)
            with self.engine.begin() as c:
                c.execute(insert_stmt)
        elif event_type in ["fallback", "optimizer"]:
            update_stmt = (
                update(publisher)
                .where(publisher.c.engine_event_id == engine_event_id)
                .values(**m)
            )
            with self.engine.begin() as c:
                c.execute(update_stmt)
        return True
