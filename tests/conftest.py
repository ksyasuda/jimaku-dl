"""Configuration and fixtures for pytest."""

import os
import tempfile
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_dir():
    """Provide a temporary directory that gets cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def mock_requests():
    """Create mocked requests functions with a response object."""
    mock_response = MagicMock()

    def mock_get(*args, **kwargs):
        return mock_response

    def mock_post(*args, **kwargs):
        return mock_response

    return {
        "get": MagicMock(side_effect=mock_get),
        "post": MagicMock(side_effect=mock_post),
        "response": mock_response,
    }


@pytest.fixture
def mock_anilist_response():
    """Create a mock response for AniList API."""
    return {
        "data": {
            "Page": {
                "media": [
                    {
                        "id": 123456,
                        "title": {
                            "english": "Test Anime",
                            "romaji": "Test Anime Romaji",
                            "native": "テストアニメ",
                        },
                        "format": "TV",
                        "episodes": 12,
                        "season": "WINTER",
                        "seasonYear": 2023,
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_jimaku_entries_response():
    """Create a mock response for Jimaku entries API."""
    return [{"id": 1, "english_name": "Test Anime", "japanese_name": "テストアニメ"}]


@pytest.fixture
def mock_jimaku_files_response():
    """Create a mock response for Jimaku files API."""
    return [
        {
            "id": 101,
            "name": "Test Anime - 01.srt",
            "url": "https://example.com/sub1.srt",
        },
        {
            "id": 102,
            "name": "Test Anime - 02.srt",
            "url": "https://example.com/sub2.srt",
        },
    ]


@pytest.fixture
def sample_video_file(temp_dir):
    """Create a sample video file for testing."""
    video_file_path = os.path.join(temp_dir, "Test Anime - S01E01.mkv")
    with open(video_file_path, "wb") as f:
        f.write(b"mock video data")
    return video_file_path


@pytest.fixture
def sample_anime_directory(temp_dir):
    """Create a sample anime directory structure for testing."""
    # Create directory structure
    anime_dir = os.path.join(temp_dir, "Test Anime")
    season_dir = os.path.join(anime_dir, "Season 1")
    os.makedirs(season_dir, exist_ok=True)

    # Add video files
    for ep in range(1, 3):
        video_path = os.path.join(season_dir, f"Test Anime - {ep:02d}.mkv")
        with open(video_path, "wb") as f:
            f.write(b"mock video data")

    return anime_dir


class MonitorFunction:
    """Helper class to monitor function calls in tests."""

    def __init__(self):
        self.called = False
        self.call_count = 0
        self.last_args = None
        self.return_value = None

    def __call__(self, *args, **kwargs):
        self.called = True
        self.call_count += 1
        self.last_args = (args, kwargs)
        if len(args) > 0:
            return args[0]  # Return first arg for chaining
        return self.return_value


@pytest.fixture
def mock_functions(monkeypatch):
    """Fixture to provide function mocking utilities."""

    @contextmanager
    def monitor_function(obj, func_name):
        """Context manager to monitor calls to a function."""
        monitor = MonitorFunction()
        original = getattr(obj, func_name, None)
        monkeypatch.setattr(obj, func_name, monitor)
        try:
            yield monitor
        finally:
            if original:
                monkeypatch.setattr(obj, func_name, original)

    return monitor_function


@pytest.fixture
def mock_user_input():
    """Provide a fixture for mocking user input consistently."""
    with patch("builtins.input") as mock_input:

        def input_sequence(*responses):
            mock_input.side_effect = responses
            return mock_input

        yield input_sequence


# Update pytest with the new MonitorFunction
setattr(pytest, "MonitorFunction", MonitorFunction)
