"""Extended test cases for the downloader module to improve coverage."""

import os
import socket
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest

from jimaku_dl.downloader import JimakuDownloader


class TestTrackDetection:
    """Tests for track detection and identification functions."""

    def test_get_track_ids_no_tracks_found(self):
        """Test get_track_ids when no tracks are found."""
        downloader = JimakuDownloader(api_token="test_token")

        # Mock subprocess output with no identifiable tracks
        mock_result = MagicMock()
        mock_result.stdout = "Some output without track information"

        with patch("jimaku_dl.downloader.subprocess_run", return_value=mock_result):
            sid, aid = downloader.get_track_ids(
                "/path/to/video.mkv", "/path/to/subtitle.srt"
            )

            assert sid is None
            assert aid is None

    def test_get_track_ids_japanese_audio_detection(self):
        """Test get_track_ids with Japanese audio detection."""
        downloader = JimakuDownloader(api_token="test_token")

        # Mock subprocess output with MPV's actual format
        mock_result = MagicMock()
        mock_result.stdout = (
            " (+) Video --vid=1 (h264 1920x1080 23.976fps)\n"
            " (+) Audio --aid=1 (aac 2ch 48000Hz) [Japanese]\n"
            " (+) Subtitle --sid=1 (subrip) [subtitle.srt]\n"
        )

        # Path to mock subtitle for basename comparison
        subtitle_path = "/path/to/subtitle.srt"

        # Mock the basename function to match what's in the output
        with patch(
            "jimaku_dl.downloader.subprocess_run", return_value=mock_result
        ), patch("jimaku_dl.downloader.basename", return_value="subtitle.srt"):

            sid, aid = downloader.get_track_ids("/path/to/video.mkv", subtitle_path)

            assert sid == 1
            assert aid == 1  # Japanese audio track

    def test_get_track_ids_fallback_to_first_audio(self):
        """Test track detection with fallback to first audio track."""
        downloader = JimakuDownloader(api_token="test_token")

        # Mock subprocess output with non-Japanese tracks in proper MPV format
        mock_result = MagicMock()
        mock_result.stdout = (
            " (+) Video --vid=1 (h264 1920x1080 23.976fps)\n"
            " (+) Audio --aid=1 (aac 2ch 48000Hz) [English]\n"
            " (+) Subtitle --sid=1 (subrip) [subtitle.srt]\n"
        )

        # Path to mock subtitle for basename comparison
        subtitle_path = "/path/to/subtitle.srt"

        # Mock the basename function to match what's in the output
        with patch(
            "jimaku_dl.downloader.subprocess_run", return_value=mock_result
        ), patch("jimaku_dl.downloader.basename", return_value="subtitle.srt"):

            sid, aid = downloader.get_track_ids("/path/to/video.mkv", subtitle_path)

            assert sid == 1
            assert aid == 1  # Fallback to first audio track


class TestMPVSocketCommunication:
    """Tests for MPV socket communication functions."""

    def test_update_mpv_subtitle_socket_error(self):
        """Test update_mpv_subtitle with socket errors."""
        downloader = JimakuDownloader(api_token="test_token")

        # Mock socket to raise connection error
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = socket.error("Connection refused")

        with patch("socket.socket", return_value=mock_sock), patch(
            "jimaku_dl.downloader.exists", return_value=True
        ), patch("jimaku_dl.downloader.time.sleep", return_value=None):

            result = downloader.update_mpv_subtitle(
                "/tmp/mpv.sock", "/path/to/subtitle.srt"
            )

            assert result is False
            mock_sock.connect.assert_called_once()

    def test_update_mpv_subtitle_nonexistent_socket(self):
        """Test update_mpv_subtitle with nonexistent socket."""
        downloader = JimakuDownloader(api_token="test_token")

        with patch("jimaku_dl.downloader.exists", return_value=False):
            result = downloader.update_mpv_subtitle(
                "/tmp/nonexistent.sock", "/path/to/subtitle.srt"
            )

            assert result is False

    def test_update_mpv_subtitle_socket_error(self):
        """Test handling of socket errors in update_mpv_subtitle."""
        downloader = JimakuDownloader(api_token="test_token")

        # Mock socket connection that fails
        with patch("socket.socket") as mock_socket:
            # Create a mock socket instance
            mock_socket_instance = MagicMock()
            mock_socket.return_value = mock_socket_instance

            # Make connect method raise an exception
            mock_socket_instance.connect.side_effect = socket.error("Connection error")

            # Call the method
            result = downloader.update_mpv_subtitle("/tmp/mpv.sock", "subtitle.srt")

            # Check that the result is False (failure)
            assert result is False
            # Verify connect was called
            mock_socket_instance.connect.assert_called_once()


class TestSubtitleSynchronization:
    """Tests for subtitle synchronization functionality."""

    def test_sync_subtitles_process_error(self):
        """Test handling of process errors in sync_subtitles."""
        downloader = JimakuDownloader(api_token="test_token")

        with patch(
            "jimaku_dl.downloader.JimakuDownloader.check_existing_sync",
            return_value=None,
        ), patch("jimaku_dl.downloader.subprocess_run") as mock_run:

            # Configure subprocess to return an error code
            process_mock = MagicMock()
            process_mock.returncode = 1
            process_mock.stderr = "ffsubsync error output"
            mock_run.return_value = process_mock

            result = downloader.sync_subtitles(
                "/path/to/video.mkv", "/path/to/subtitle.srt", "/path/to/output.srt"
            )

            # Should return the original subtitle path on error
            assert result == "/path/to/subtitle.srt"

    def test_sync_subtitles_ffsubsync_not_found(self):
        """Test handling when ffsubsync command is not found."""
        downloader = JimakuDownloader(api_token="test_token")

        with patch(
            "jimaku_dl.downloader.JimakuDownloader.check_existing_sync",
            return_value=None,
        ), patch(
            "jimaku_dl.downloader.subprocess_run",
            side_effect=FileNotFoundError("No such file or command"),
        ):

            result = downloader.sync_subtitles(
                "/path/to/video.mkv", "/path/to/subtitle.srt"
            )

            # Should return the original subtitle path
            assert result == "/path/to/subtitle.srt"


class TestFileNameParsing:
    """Tests for file and directory name parsing functionality."""

    def test_parse_filename_with_special_characters(self):
        """Test parse_filename with special characters in the filename."""
        downloader = JimakuDownloader(api_token="test_token")

        # Test with parentheses and brackets
        title, season, episode = downloader.parse_filename(
            "Show Name (2023) - S01E05 [1080p][HEVC].mkv"
        )
        assert title == "Show Name (2023)"
        assert season == 1
        assert episode == 5

    def test_parse_directory_name_normalization(self):
        """Test directory name parsing with normalization."""
        downloader = JimakuDownloader(api_token="test_token")

        # Test with underscores and dots
        success, title, season, episode = downloader.parse_directory_name(
            "/path/to/Show_Name.2023"
        )
        assert success is True
        assert title == "Show Name 2023"
        assert season == 1
        assert episode == 0

    def test_find_anime_title_in_path_hierarchical(self):
        """Test finding anime title in hierarchical directory structure."""
        downloader = JimakuDownloader(api_token="test_token")

        # Create a mock implementation of parse_directory_name
        results = {
            "/path/to/Anime/Winter 2023/Show Name/Season 1": (False, "", 0, 0),
            "/path/to/Anime/Winter 2023/Show Name": (True, "Show Name", 1, 0),
            "/path/to/Anime/Winter 2023": (False, "", 0, 0),
            "/path/to/Anime": (False, "", 0, 0),
        }

        def mock_parse_directory_name(path):
            return results.get(path, (False, "", 0, 0))

        # Apply the mock and test
        with patch.object(
            downloader, "parse_directory_name", mock_parse_directory_name
        ):
            title, season, episode = downloader.find_anime_title_in_path(
                "/path/to/Anime/Winter 2023/Show Name/Season 1"
            )

            assert title == "Show Name"
            assert season == 1
            assert episode == 0

    def test_find_anime_title_in_path_hierarchical(self):
        """Test finding anime title in a hierarchical directory structure."""
        downloader = JimakuDownloader(api_token="test_token")

        # Use os.path.join for cross-platform compatibility
        hierarchical_path = os.path.join(
            "path", "to", "Anime", "Winter 2023", "Show Name", "Season 1"
        )

        # Mock parse_directory_name to return specific values at different levels
        with patch.object(downloader, "parse_directory_name") as mock_parse:
            # Return values for each level going up from Season 1 to Anime
            mock_parse.side_effect = [
                (False, "", 0, 0),  # Fail for "Season 1"
                (True, "Show Name", 1, 0),  # Succeed for "Show Name"
                (False, "", 0, 0),  # Fail for "Winter 2023"
                (False, "", 0, 0),  # Fail for "Anime"
            ]

            title, season, episode = downloader.find_anime_title_in_path(
                hierarchical_path
            )

            assert title == "Show Name"
            assert season == 1
            assert episode == 0


class TestEdgeCases:
    """Tests for edge cases and error handling in the downloader."""

    def test_filter_files_by_episode_special_patterns(self):
        """Test filtering subtitles with special episode patterns."""
        downloader = JimakuDownloader(api_token="test_token")

        # Test files with various patterns
        files = [
            {"id": 1, "name": "Show - 01.srt"},
            {"id": 2, "name": "Show - Episode 02.srt"},
            {"id": 3, "name": "Show - E03.srt"},
            {"id": 4, "name": "Show - Ep 04.srt"},
            {"id": 5, "name": "Show #05.srt"},
            {"id": 6, "name": "Show - 06v2.srt"},
            {"id": 7, "name": "Show (Complete).srt"},
            {"id": 8, "name": "Show - Batch.srt"},
        ]

        # Filter for episode 3
        filtered = downloader.filter_files_by_episode(files, 3)
        assert len(filtered) > 0
        assert filtered[0]["id"] == 3

        # Filter for episode 5
        filtered = downloader.filter_files_by_episode(files, 5)
        assert len(filtered) > 0
        assert filtered[0]["id"] == 5

        # Filter for non-existent episode - should return batch files only
        filtered = downloader.filter_files_by_episode(files, 10)
        assert len(filtered) == 2
        assert all(file["id"] in [7, 8] for file in filtered)
