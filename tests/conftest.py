import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pytest  # noqa: E402

from warcraft_survivors.content import load_content  # noqa: E402


@pytest.fixture(scope="session")
def content():
    return load_content()
