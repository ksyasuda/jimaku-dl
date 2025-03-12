"""Tests for downloading subtitles with mocked API responses."""

import os
from unittest.mock import MagicMock, patch

import pytest
import responses

from jimaku_dl.downloader import JimakuDownloader


class TestMockDownload:
    """Test downloading subtitles with mocked API responses."""

    @responses.activate
    def test_download_subtitle_flow(self, temp_dir, monkeypatch):
        """Test the full subtitle download flow with mocked responses."""
        # Set up test environment
        monkeypatch.setenv("TESTING", "1")
        video_file = os.path.join(temp_dir, "test_video.mkv")
        with open(video_file, "w") as f:
            f.write("fake video content")

        # Mock AniList API response with proper structure
        responses.add(
            responses.POST,
            "https://graphql.anilist.co",
            json={
                "data": {
                    "Page": {
                        "media": [
                            {
                                "id": 123456,
                                "title": {
                                    "english": "Test Anime",
                                    "romaji": "Test Anime",
                                    "native": "テストアニメ",
                                },
                                "format": "TV",
                                "episodes": 12,
                                "seasonYear": 2023,
                                "season": "WINTER",
                            }
                        ]
                    }
                }
            },
            status=200,
        )

        # Mock Jimaku search API
        responses.add(
            responses.GET,
            "https://jimaku.cc/api/entries/search",
            json=[
                {
                    "id": 100,
                    "english_name": "Test Anime",
                    "japanese_name": "テストアニメ",
                }
            ],
            status=200,
        )

        # Mock Jimaku files API
        responses.add(
            responses.GET,
            "https://jimaku.cc/api/entries/100/files",
            json=[
                {
                    "id": 200,
                    "name": "test.srt",
                    "url": "https://jimaku.cc/download/test.srt",
                }
            ],
            status=200,
        )

        # Mock file download
        responses.add(
            responses.GET,
            "https://jimaku.cc/download/test.srt",
            body="1\n00:00:01,000 --> 00:00:05,000\nTest subtitle",
            status=200,
        )

        # Mock the interactive menu selections
        downloader = JimakuDownloader(api_token="test_token")
        with patch.object(downloader, "fzf_menu") as mock_fzf:
            mock_fzf.side_effect = [
                "1. Test Anime - テストアニメ",  # Select entry
                "1. test.srt",  # Select file
            ]

            # Mock parse_filename to avoid prompting
            with patch.object(
                downloader, "parse_filename", return_value=("Test Anime", 1, 1)
            ):
                # Execute the download
                result = downloader.download_subtitles(video_file)

                # Verify the result
                assert len(result) == 1
                assert "test.srt" in result[0]

    @responses.activate
    def test_error_handling(self, temp_dir, monkeypatch):
        """Test error handling when AniList API fails."""
        # Set up test environment
        monkeypatch.setenv("TESTING", "1")
        video_file = os.path.join(temp_dir, "test_video.mkv")
        with open(video_file, "w") as f:
            f.write("fake video content")

        # Mock AniList API with an error response
        responses.add(
            responses.POST,
            "https://graphql.anilist.co",
            status=404,  # Simulate 404 error
        )

        # Create downloader and attempt to download
        downloader = JimakuDownloader(api_token="test_token")
        with patch.object(
            downloader, "parse_filename", return_value=("Test Anime", 1, 1)
        ):
            with pytest.raises(ValueError) as exc_info:
                downloader.download_subtitles(video_file)

            # Check for the specific error message now
            assert "Network error querying AniList API" in str(exc_info.value)

    @responses.activate
    def test_unauthorized_api_error(self, temp_dir, monkeypatch):
        """Test error handling when Jimaku API returns unauthorized."""
        # Set up test environment
        monkeypatch.setenv("TESTING", "1")
        video_file = os.path.join(temp_dir, "test_video.mkv")
        with open(video_file, "w") as f:
            f.write("fake video content")

        # Mock AniList API response with success to get past that check
        responses.add(
            responses.POST,
            "https://graphql.anilist.co",
            json={
                "data": {
                    "Page": {
                        "media": [
                            {
                                "id": 123456,
                                "title": {
                                    "english": "Test Anime",
                                    "romaji": "Test Anime",
                                    "native": "テストアニメ",
                                },
                            }
                        ]
                    }
                }
            },
            status=200,
        )

        # Mock Jimaku search API with 401 unauthorized error
        responses.add(
            responses.GET,
            "https://jimaku.cc/api/entries/search",
            json={"error": "Unauthorized"},
            status=401,
        )

        # Create downloader and attempt to download
        downloader = JimakuDownloader(api_token="invalid_token")
        with patch.object(
            downloader, "parse_filename", return_value=("Test Anime", 1, 1)
        ):
            with pytest.raises(ValueError) as exc_info:
                downloader.download_subtitles(video_file)

            # Now check for the Jimaku API error
            assert "Error querying Jimaku API" in str(exc_info.value)

    @responses.activate
    def test_no_subtitle_entries_found(self, temp_dir, monkeypatch):
        """Test handling when no subtitle entries are found."""
        # Set up test environment
        monkeypatch.setenv("TESTING", "1")
        video_file = os.path.join(temp_dir, "test_video.mkv")
        with open(video_file, "w") as f:
            f.write("fake video content")

        # Mock AniList API response with success
        responses.add(
            responses.POST,
            "https://graphql.anilist.co",
            json={
                "data": {
                    "Page": {
                        "media": [
                            {
                                "id": 123456,
                                "title": {
                                    "english": "Test Anime",
                                    "romaji": "Test Anime",
                                    "native": "テストアニメ",
                                },
                            }
                        ]
                    }
                }
            },
            status=200,
        )

        # Mock Jimaku search API with empty response (no entries)
        responses.add(
            responses.GET,
            "https://jimaku.cc/api/entries/search",
            json=[],  # Empty array indicates no entries found
            status=200,
        )

        # Create downloader and attempt to download
        downloader = JimakuDownloader(api_token="test_token")
        with patch.object(
            downloader, "parse_filename", return_value=("Test Anime", 1, 1)
        ):
            with pytest.raises(ValueError) as exc_info:
                downloader.download_subtitles(video_file)

            assert "No subtitle entries found" in str(exc_info.value)

    @responses.activate
    def test_no_subtitle_files_found(self, temp_dir, monkeypatch):
        """Test handling when no subtitle files are available for an entry."""
        # Set up test environment
        monkeypatch.setenv("TESTING", "1")
        video_file = os.path.join(temp_dir, "test_video.mkv")
        with open(video_file, "w") as f:
            f.write("fake video content")

        # Mock AniList API response with success
        responses.add(
            responses.POST,
            "https://graphql.anilist.co",
            json={
                "data": {
                    "Page": {
                        "media": [
                            {
                                "id": 123456,
                                "title": {
                                    "english": "Test Anime",
                                    "romaji": "Test Anime",
                                    "native": "テストアニメ",
                                },
                            }
                        ]
                    }
                }
            },
            status=200,
        )

        # Mock Jimaku search API with entries
        responses.add(
            responses.GET,
            "https://jimaku.cc/api/entries/search",
            json=[
                {
                    "id": 100,
                    "english_name": "Test Anime",
                    "japanese_name": "テストアニメ",
                }
            ],
            status=200,
        )

        # Mock Jimaku files API with empty files
        responses.add(
            responses.GET,
            "https://jimaku.cc/api/entries/100/files",
            json=[],  # Empty array = no files
            status=200,
        )

        # Create downloader and attempt to download
        downloader = JimakuDownloader(api_token="test_token")
        with patch.object(downloader, "fzf_menu") as mock_fzf:
            # Mock entry selection
            mock_fzf.return_value = "1. Test Anime - テストアニメ"

            with patch.object(
                downloader, "parse_filename", return_value=("Test Anime", 1, 1)
            ):
                with pytest.raises(ValueError) as exc_info:
                    downloader.download_subtitles(video_file)

                assert "No files found" in str(exc_info.value)
