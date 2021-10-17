from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.base import Engine

from core.logging import logger
from engine.consumer import Consumer
from engine.data_models import BundleMessage
from engine.producer import Producer
from engine.stateful.pg_config import collector, get_eng, init_schema, metadata_obj


@dataclass
class PGConsumer(Consumer):
    engine: Engine = get_eng()

    def __post_init__(self) -> None:
        self.engine: Engine = get_eng()
        init_schema(self.engine)
        # TODO: are there implications of "if not exists"?
        metadata_obj.create_all(self.engine)

    def consume(
        self, queue_name: str = None, timeout: float = 60, poll_interval: float = 1
    ) -> BundleMessage:
        now = str(datetime.now())
        conn = self.engine.connect()
        query = select(collector).filter(
            or_(collector.c.timeout >= now, collector.c.optimizer_id != None)
        )
        records = [row._mapping for row in conn.execute(query)]

        for r in records:
            print(r)

        conn.close()

    def delete_message(self, queue_name: str, message_id: str = None) -> bool:
        return True


@dataclass
class PGProducer(Producer):
    def __post_init__(self) -> None:
        # TODO: are there implications of "if not exists"?
        self.engine: Engine = get_eng()
        init_schema(self.engine)
        metadata_obj.create_all(self.engine)

    def produce(self, queue_name: str, message: BundleMessage) -> bool:
        m = message.message
        event_type = m.pop("event_type")
        engine_event_id = m["engine_event_id"]
        logger.info(m)
        if event_type == "triage":
            insert_stmt = insert(collector).values(**m)
            with self.engine.begin() as c:
                c.execute(insert_stmt)
        elif event_type in ["fallback", "optimizer"]:
            update_stmt = (
                update(collector)
                .where(collector.c.engine_event_id == engine_event_id)
                .values(**m)
            )
            with self.engine.begin() as c:
                c.execute(update_stmt)
        return True


# def get_triage_data() -> BundleMessage:
#     return BundleMessage(
#         message_id = str(uuid4()),
#         params = {},
#         message = {
#             "event_type": "triage",
#             "engine_event_id": str(uuid4()),
#             "bundle_event_id": str(uuid4()),
#             "store_id": str(uuid4()),
#             "timeout": datetime.now() + timedelta(minutes=10),
#         }
#     )


# def get_opt_data(triage_data: dict) -> BundleMessage:
#     return BundleMessage(
#         message_id = str(uuid4()),
#         params = {},
#         message = {
#             "event_type": "optimizer",
#             "engine_event_id": triage_data["message"]["engine_event_id"],
#             "optimizer_id": str(uuid4()),
#             "optimizer_results": {"opt": "results"},
#             "optimizer_finish": datetime.now(),
#         }
#     )


# def get_fallback_data(triage_data: dict) -> BundleMessage:
#     return BundleMessage(
#         message_id = str(uuid4()),
#         params = {},
#         message = {
#             "event_type": "fallback",
#             "engine_event_id": triage_data["message"]["engine_event_id"],
#             "fallback_id": str(uuid4()),
#             "fallback_results": {"fallback": "results"},
#             "fallback_finish": datetime.now(),
#         }
#     )


# p = PGProducer()

# while True:
#     t = get_triage_data()
#     f = get_fallback_data(t.dict())
#     o = get_opt_data(t.dict())

#     # TRIAGE (insert only)
#     p.produce(queue_name="", message=t)
#     time.sleep(5)

#     # FALLBACK (update only)
#     p.produce(queue_name="", message=f)
#     time.sleep(5)

#     # OPTIMIZER (update only)
#     p.produce(queue_name="", message=o)

#     time.sleep(5)
