# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

import pytest
from uuid import uuid4

from hoja.app.models import HojaAction, HojaObservation, HojaState
from hoja.app.environment import HojaEnvironment


@pytest.fixture
def env():
    """Returns a fresh Medium difficulty environment."""
    import os
    os.environ["HOJA_TASK"] = "medium"
    return HojaEnvironment()
