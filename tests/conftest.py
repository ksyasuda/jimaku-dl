"""Test configuration and fixtures for jimaku-dl."""

import builtins
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import responses


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def sample_video_file(temp_dir):
    """Create a sample video file for testing."""
    video_file = os.path.join(temp_dir, "test_video.mkv")
    with open(video_file, "wb") as f:
        f.write(b"fake video content")
    return video_file


@pytest.fixture
def sample_anime_directory(temp_dir):
    """Create a sample anime directory structure for testing."""
    anime_dir = os.path.join(temp_dir, "Test Anime")
    os.makedirs(anime_dir, exist_ok=True)
    season_dir = os.path.join(anime_dir, "Season 1")
    os.makedirs(season_dir, exist_ok=True)

    # Create a few dummy video files
    for i in range(1, 4):
        video_file = os.path.join(season_dir, f"Episode {i}.mkv")
        with open(video_file, "wb") as f:
            f.write(b"fake video content")

    return anime_dir


@pytest.fixture
def mock_requests():
    """Set up common request mocking."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None

    mock_post = MagicMock(return_value=mock_response)
    mock_get = MagicMock(return_value=mock_response)

    with patch("requests.post", mock_post), patch("requests.get", mock_get), patch(
        "jimaku_dl.downloader.requests_post", mock_post
    ), patch("jimaku_dl.downloader.requests_get", mock_get):
        yield {"post": mock_post, "get": mock_get, "response": mock_response}


@pytest.fixture
def mock_anilist_response():
    """Mock response for AniList API."""
    return {
        "data": {
            "Page": {
                "media": [
                    {
                        "id": 123456,
                        "title": {
                            "english": "Test Anime Show",
                            "romaji": "Test Anime",
                            "native": "テストアニメ",
                        },
                        "synonyms": ["Test Show"],
                        "format": "TV",
                        "episodes": 12,
                        "seasonYear": 2023,
                        "season": "WINTER",
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_jimaku_entries_response():
    """Return a mock response for Jimaku entries API."""
    return [
        {"id": 100, "english_name": "Test Anime", "japanese_name": "テストアニメ"},
        {
            "id": 101,
            "english_name": "Another Test Anime",
            "japanese_name": "別のテストアニメ",
        },
    ]


@pytest.fixture
def mock_jimaku_files_response():
    """Return a mock response for Jimaku files API."""
    return [
        {
            "id": 201,
            "name": "Test Anime - 01.srt",
            "url": "https://example.com/subtitles/201",
        },
        {
            "id": 202,
            "name": "Test Anime - 02.srt",
            "url": "https://example.com/subtitles/202",
        },
    ]


@pytest.fixture
def setup_test_environment():
    """Set up a complete test environment with all mocks for API testing."""
    # Mark this as a test environment
    os.environ["TESTING"] = "1"

    # Create patchers
    path_exists_patcher = patch("os.path.exists", return_value=True)
    open_patcher = patch("builtins.open", mock_open(read_data="test data"))
    input_patcher = patch("builtins.input", return_value="Test Input")
    subprocess_patcher = patch(
        "subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")
    )

    # Add responses for API endpoints
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        # Mock AniList API
        rsps.add(
            responses.POST,
            "https://graphql.anilist.co",
            json={"data": {"Media": {"id": 1234}}},
            status=200,
        )

        # Mock Jimaku search endpoint with ?anilist_id parameter
        rsps.add(
            responses.GET,
            "https://jimaku.cc/api/entries/search",
            match=[responses.matchers.query_param_matcher({"anilist_id": "1234"})],
            json=[
                {
                    "id": 100,
                    "english_name": "Test Anime",
                    "japanese_name": "テスト",
                }
            ],
            status=200,
        )

        # Mock Jimaku files endpoint
        rsps.add(
            responses.GET,
            "https://jimaku.cc/api/entries/100/files",
            json=[
                {
                    "id": 200,
                    "name": "Test Anime - 01.srt",
                    "url": "https://jimaku.cc/download/200",
                }
            ],
            status=200,
        )

        # Mock subtitle file download
        rsps.add(
            responses.GET,
            "https://jimaku.cc/download/200",
            body="1\n00:00:01,000 --> 00:00:05,000\nTest subtitle",
            status=200,
        )

        # Start patchers
        path_exists = path_exists_patcher.start()
        mock_open_file = open_patcher.start()
        mock_input = input_patcher.start()
        mock_subprocess = subprocess_patcher.start()

        yield {
            "path_exists": path_exists,
            "mock_open": mock_open_file,
            "mock_input": mock_input,
            "mock_subprocess": mock_subprocess,
            "rsps": rsps,
        }

        # Stop patchers
        path_exists_patcher.stop()
        open_patcher.stop()
        input_patcher.stop()
        subprocess_patcher.stop()

    # Clean up environment
    del os.environ["TESTING"]
