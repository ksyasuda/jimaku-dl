"""Tests for downloading subtitles with mocked API responses."""

import os
from unittest.mock import patch, MagicMock

import pytest
import responses

from jimaku_dl.downloader import JimakuDownloader


class TestMockDownload:
    """Test downloading subtitles with mocked API."""

    @responses.activate
    def test_download_subtitle_flow(self, setup_test_environment, temp_dir):
        """Test the complete download flow with mocked API."""
        # Create a temp file path that will pass the exists check
        media_path = os.path.join(temp_dir, "anime.mkv")
        with open(media_path, "w") as f:
            f.write("dummy content")

        # Add a specific response for the exact GraphQL request we'll make
        responses.add(
            responses.POST,
            "https://graphql.anilist.co",
            json={"data": {"Media": {"id": 1234}}},
            status=200,
        )

        # Add response for Jimaku entry search
        responses.add(
            responses.GET,
            "https://jimaku.cc/api/entries/search",
            match=[responses.matchers.query_param_matcher({"anilist_id": "1234"})],
            json=[{"id": 100, "english_name": "Test Anime", "japanese_name": "テスト"}],
            status=200,
        )

        # Add response for Jimaku file list
        responses.add(
            responses.GET,
            "https://jimaku.cc/api/entries/100/files",
            json=[
                {
                    "id": 200,
                    "name": "Test Anime - 01.srt",
                    "url": "https://example.com/file.srt",
                }
            ],
            status=200,
        )

        # Create downloader with mocked fzf_menu
        downloader = JimakuDownloader(api_token="test_token")

        with patch.object(
            downloader, "fzf_menu", side_effect=lambda options, multi=False: options[0]
        ), patch.object(
            downloader,
            "download_file",
            return_value=os.path.join(temp_dir, "Test Anime - 01.srt"),
        ), patch.object(
            downloader, "parse_filename", return_value=("Test Anime", 1, 1)
        ), patch(
            "os.path.exists", return_value=True
        ), patch(
            "jimaku_dl.downloader.exists", return_value=True
        ), patch(
            "builtins.input", return_value="1"
        ):  # Handle any user input prompts

            # Test with file path
            result = downloader.download_subtitles(
                media_path=media_path, dest_dir=temp_dir
            )

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == os.path.join(temp_dir, "Test Anime - 01.srt")

    @responses.activate
    def test_error_handling(self, setup_test_environment, temp_dir):
        """Test error handling with mocked API errors."""
        # Setup mocked API response with error
        responses.add(
            responses.POST,
            "https://graphql.anilist.co",
            json={"errors": [{"message": "Not found"}]},
            status=404,
        )

        # Create a temp file that exists
        media_path = os.path.join(temp_dir, "anime.mkv")
        with open(media_path, "w") as f:
            f.write("dummy content")

        downloader = JimakuDownloader(api_token="test_token")

        # Mock parse_filename to return known values
        with patch.object(
            downloader, "parse_filename", return_value=("Test Anime", 1, 1)
        ), patch("os.path.exists", return_value=True), patch(
            "jimaku_dl.downloader.exists", return_value=True
        ), pytest.raises(
            ValueError
        ) as exc_info:

            downloader.download_subtitles(media_path=media_path)

        assert "Error querying AniList API" in str(exc_info.value)

    @responses.activate
    def test_unauthorized_api_error(self, setup_test_environment, temp_dir):
        """Test handling of unauthorized API errors."""
        # Create a temp file that exists
        media_path = os.path.join(temp_dir, "anime.mkv")
        with open(media_path, "w") as f:
            f.write("dummy content")

        # Setup mocked API response with 401 error
        responses.add(
            responses.POST,
            "https://graphql.anilist.co",
            json={"data": {"Media": {"id": 1234}}},
            status=200,
        )

        responses.add(
            responses.GET,
            "https://jimaku.cc/api/entries/search",
            match=[responses.matchers.query_param_matcher({"anilist_id": "1234"})],
            status=401,
            json={"error": "Unauthorized"},
        )

        downloader = JimakuDownloader(api_token="invalid_token")

        # Mock parse_filename to return known values
        with patch.object(
            downloader, "parse_filename", return_value=("Test Anime", 1, 1)
        ), patch("os.path.exists", return_value=True), patch(
            "jimaku_dl.downloader.exists", return_value=True
        ), pytest.raises(
            ValueError
        ) as exc_info:

            downloader.download_subtitles(media_path=media_path)

        assert "Error querying Jimaku API" in str(exc_info.value)

    @responses.activate
    def test_anilist_id_from_argument(self, setup_test_environment, temp_dir):
        """Test using AniList ID provided as argument."""
        # Create a temp file that exists
        media_path = os.path.join(temp_dir, "anime.mkv")
        with open(media_path, "w") as f:
            f.write("dummy content")

        # Add Jimaku API response for entry search with specific anilist_id
        responses.add(
            responses.GET,
            "https://jimaku.cc/api/entries/search",
            match=[responses.matchers.query_param_matcher({"anilist_id": "5678"})],
            json=[{"id": 100, "english_name": "Test Anime", "japanese_name": "テスト"}],
            status=200,
        )

        # No need to add the files endpoint since it won't be called when fzf_menu returns None

        downloader = JimakuDownloader(api_token="test_token")

        with patch.object(
            downloader, "parse_filename", return_value=("Test Anime", 1, 1)
        ), patch.object(downloader, "fzf_menu", return_value=None), patch(
            "os.path.exists", return_value=True
        ), patch(
            "jimaku_dl.downloader.exists", return_value=True
        ):
            # Should raise ValueError due to no selection in fzf
            with pytest.raises(ValueError):
                downloader.download_subtitles(media_path=media_path, anilist_id=5678)

        # Check that the expected call was made
        assert len(responses.calls) > 0

        # Check that at least one call was to the expected URL with the anilist_id parameter
        jimaku_calls = [
            call
            for call in responses.calls
            if "jimaku.cc/api/entries/search" in call.request.url
        ]
        assert len(jimaku_calls) > 0
        assert "anilist_id=5678" in jimaku_calls[0].request.url
