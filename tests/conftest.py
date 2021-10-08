import pytest

import os

os.environ["INPUT_QUEUE"] = "input"
os.environ["OUTPUT_QUEUE"] = "output"
os.environ["REDIS_HOST"] = "redis"