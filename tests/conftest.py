"""Global pytest fixtures for jimaku-dl tests."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def mock_anilist_response():
    """Mock response from AniList API."""
    return {
        "data": {
            "Media": {
                "id": 123456,
                "title": {
                    "romaji": "Test Anime",
                    "english": "Test Anime English",
                    "native": "テストアニメ",
                },
                "synonyms": ["Test Show"],
            }
        }
    }


@pytest.fixture
def mock_jimaku_entries_response():
    """Mock response from Jimaku entries endpoint."""
    return [
        {
            "id": 1,
            "english_name": "Test Anime",
            "japanese_name": "テストアニメ",
            "anilist_id": 123456,
        }
    ]


@pytest.fixture
def mock_jimaku_files_response():
    """Mock response from Jimaku files endpoint."""
    return [
        {
            "id": 101,
            "name": "Test Anime - 01.srt",
            "url": "https://jimaku.cc/api/files/101",
        },
        {
            "id": 102,
            "name": "Test Anime - 02.srt",
            "url": "https://jimaku.cc/api/files/102",
        },
    ]


@pytest.fixture
def mock_requests(
    monkeypatch,
    mock_anilist_response,
    mock_jimaku_entries_response,
    mock_jimaku_files_response,
):
    """Mock requests module for API calls."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock()

    def mock_requests_post(url, **kwargs):
        if "anilist.co" in url:
            mock_response.json.return_value = mock_anilist_response
        return mock_response

    def mock_requests_get(url, **kwargs):
        if "entries/search" in url:
            mock_response.json.return_value = mock_jimaku_entries_response
        elif "entries/" in url and "/files" in url:
            mock_response.json.return_value = mock_jimaku_files_response
        return mock_response

    # Patch both the direct imports used in downloader.py and the regular requests module
    monkeypatch.setattr("requests.post", mock_requests_post)
    monkeypatch.setattr("requests.get", mock_requests_get)
    monkeypatch.setattr("jimaku_dl.downloader.requests_post", mock_requests_post)
    monkeypatch.setattr("jimaku_dl.downloader.requests_get", mock_requests_get)

    return {
        "post": mock_requests_post,
        "get": mock_requests_get,
        "response": mock_response,
    }


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess module for fzf and mpv calls."""
    mock_run = MagicMock()
    mock_result = MagicMock()
    mock_result.stdout = "1. Test Selection"
    mock_run.return_value = mock_result

    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def sample_video_file(temp_dir):
    """Create a sample video file."""
    file_path = os.path.join(temp_dir, "Test Anime S01E01 [1080p].mkv")
    with open(file_path, "wb") as f:
        f.write(b"dummy video content")
    return file_path


@pytest.fixture
def sample_anime_directory(temp_dir):
    """Create a sample directory structure for anime."""
    # Main directory
    anime_dir = os.path.join(temp_dir, "Test Anime")
    os.makedirs(anime_dir)

    # Season subdirectory
    season_dir = os.path.join(anime_dir, "Season-1")
    os.makedirs(season_dir)

    # Episode files
    for i in range(1, 3):
        file_path = os.path.join(season_dir, f"Test Anime S01E0{i} [1080p].mkv")
        with open(file_path, "wb") as f:
            f.write(b"dummy video content")

    return anime_dir


@pytest.fixture(autouse=True)
def clean_mocks():
    """Reset all mocks after each test to prevent side effect leakage."""
    yield
    # This runs after each test to clean up
    from unittest import mock
    
    # Get all active patches and stop them
    mock.patch.stopall()
    
    # Clear mock registry
    mock._patch._active_patches.clear()
    
    # Create clean mock for JimakuDownloader methods that are commonly patched
    clean_download_mock = mock.MagicMock()
    clean_download_mock.side_effect = None  # Ensure no side effects are set
    clean_download_mock.return_value = ["/path/to/clean_subtitle.srt"]
    
    # Patch the common methods with clean mocks
    test_patches = [
        mock.patch('jimaku_dl.cli.JimakuDownloader'),
        mock.patch('jimaku_dl.cli.parse_args')
    ]
    
    # Start all patches
    for test_patch in test_patches:
        test_patch.start()
