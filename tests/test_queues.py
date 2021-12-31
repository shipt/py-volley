import pytest

from volley.profiles import Profile
from volley.queues import Queue
from volley.serializers.base import NullSerializer


def test_bad_type(confluent_consumer_profile: Profile) -> None:
    q = Queue(
        name="test",
        value="long_value",
        profile=confluent_consumer_profile,
        pass_through_config="bad_value",  # type: ignore
    )

    with pytest.raises(TypeError):
        q.connect("BAD_TYPE")  # type: ignore
