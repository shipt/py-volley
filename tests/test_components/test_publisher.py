from datetime import datetime, timedelta

import pytest
import pytz

from components.collector import main as collector
from components.data_models import (
    CollectFallback,
    CollectOptimizer,
    CollectTriage,
    OutputMessage,
    PublisherMessage,
)
from components.publisher import TimeoutError
from components.publisher import main as publisher


def test_publisher_optimizer(publisher_complete_message: PublisherMessage) -> None:
    t_outputs = publisher.__wrapped__(publisher_complete_message)
    for qname, m in t_outputs:
        assert m.optimizer_type == "optimizer"
        assert isinstance(m, OutputMessage)


def test_collector_publisher(
    collector_optimizer_message: CollectOptimizer,
    collector_fallback_message: CollectFallback,
    collector_triage_message: CollectTriage,
) -> None:
    f = collector.__wrapped__(collector_fallback_message)
    o = collector.__wrapped__(collector_optimizer_message)
    t = collector.__wrapped__(collector_triage_message)
    for i in [f, o, t]:
        for _i in i:
            assert _i[0] == "publisher"


def test_publisher_fallback(publisher_complete_message: PublisherMessage) -> None:
    pub_dict = publisher_complete_message.dict()
    # remove the optimizer results from the example data
    del pub_dict["results"][0]["optimizer_finish"]
    del pub_dict["results"][0]["optimizer_results"]
    del pub_dict["results"][0]["optimizer_id"]

    # assert message is parsed as a "fallback" solution
    msg = PublisherMessage.parse_obj(pub_dict)
    t_outputs = publisher.__wrapped__(msg)
    for qname, m in t_outputs:
        assert m.optimizer_type == "fallback"
        assert isinstance(m, OutputMessage)


def test_publisher_error(publisher_complete_message: PublisherMessage) -> None:
    pub_dict = publisher_complete_message.dict()
    del pub_dict["results"][0]["optimizer_finish"]
    del pub_dict["results"][0]["optimizer_results"]
    del pub_dict["results"][0]["optimizer_id"]
    del pub_dict["results"][0]["fallback_finish"]
    del pub_dict["results"][0]["fallback_results"]
    del pub_dict["results"][0]["fallback_id"]
    pub_dict["results"][0]["timeout"] = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(minutes=1)
    msg = PublisherMessage.parse_obj(pub_dict)

    with pytest.raises(TimeoutError):
        t_outputs = publisher.__wrapped__(msg)


def test_publisher_error_not_expired(publisher_complete_message: PublisherMessage) -> None:
    pub_dict = publisher_complete_message.dict()
    del pub_dict["results"][0]["optimizer_finish"]
    del pub_dict["results"][0]["optimizer_results"]
    del pub_dict["results"][0]["optimizer_id"]
    del pub_dict["results"][0]["fallback_finish"]
    del pub_dict["results"][0]["fallback_results"]
    del pub_dict["results"][0]["fallback_id"]
    msg = PublisherMessage.parse_obj(pub_dict)

    t_outputs = publisher.__wrapped__(msg)
    assert not t_outputs
