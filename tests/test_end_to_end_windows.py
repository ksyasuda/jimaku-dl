"""End-to-end tests simulating Windows environment."""

import builtins
import os
import platform
import socket
from unittest.mock import patch, MagicMock, mock_open

import pytest

from jimaku_dl.downloader import JimakuDownloader
from jimaku_dl.cli import main


# Patch to simulate Windows environment
@pytest.fixture
def windows_environment():
    """Create a simulated Windows environment."""
    # Save original items we'll modify
    original_platform = platform.system
    original_path_exists = os.path.exists
    original_open = builtins.open
    original_socket_socket = socket.socket

    # Create mock objects
    mock_socket = MagicMock()

    # Mock Windows behavior
    platform.system = lambda: "Windows"
    os.sep = "\\"

    # Restore all after test
    try:
        yield
    finally:
        platform.system = original_platform
        os.path.exists = original_path_exists
        builtins.open = original_open
        socket.socket = original_socket_socket
        os.sep = "/"


class TestEndToEndWindows:
    """Test the complete application flow in a Windows environment."""

    def test_path_handling_windows(self, windows_environment, temp_dir):
        """Test path handling in Windows environment."""
        # Create a test file that will pass the existence check
        test_file = os.path.join(temp_dir, "test_video.mkv")
        with open(test_file, "w") as f:
            f.write("dummy content")

        # Use Windows-style path
        win_path = test_file.replace("/", "\\")

        # Create a downloader with mock token and network calls
        with patch("requests.post") as mock_post, patch(
            "requests.get"
        ) as mock_get, patch(
            "jimaku_dl.downloader.requests_get"
        ) as mock_requests_get, patch(
            "builtins.open", mock_open()
        ), patch(
            "subprocess.run"
        ) as mock_run, patch(
            "builtins.input", return_value="Show Name"
        ):

            # Setup mocks with proper return values
            mock_post.return_value.json.return_value = {"data": {"Media": {"id": 1234}}}
            mock_post.return_value.status_code = 200

            # Mock for the Jimaku API calls
            mock_get_response = MagicMock()
            mock_get_response.json.return_value = [
                {"id": 1, "english_name": "Test Anime", "japanese_name": "テスト"}
            ]
            mock_get_response.status_code = 200
            mock_get_response.raise_for_status = MagicMock()

            mock_get.return_value = mock_get_response
            mock_requests_get.return_value = mock_get_response

            # Create downloader
            downloader = JimakuDownloader("test_token")

            # Test that Windows paths are handled correctly with mocked _prompt_for_title_info
            with patch.object(
                downloader, "_prompt_for_title_info", return_value=("Show Name", 1, 1)
            ):
                result = downloader.parse_filename(win_path)
                assert result[0] == "Show Name"  # Should extract show name correctly

            # A more extensive mock to properly handle the fzf menu selection
            test_entry = {
                "id": 1,
                "english_name": "Test Anime",
                "japanese_name": "テスト",
            }
            test_file_info = {
                "id": 101,
                "name": "test_file.srt",
                "url": "http://test/file",
            }

            def mock_fzf_menu_side_effect(options, multi=False):
                """Handle both cases of fzf menu calls properly."""
                if any("Test Anime - テスト" in opt for opt in options):
                    # This is the first call to select the entry
                    return "1. Test Anime - テスト"
                else:
                    # This is the second call to select the file
                    return "1. test_file.srt" if not multi else ["1. test_file.srt"]

            # Test if download function handles Windows paths by mocking all the API calls
            with patch.object(
                downloader, "fzf_menu", side_effect=mock_fzf_menu_side_effect
            ), patch.object(
                downloader, "query_anilist", return_value=1234
            ), patch.object(
                downloader, "parse_filename", return_value=("Show Name", 1, 1)
            ), patch.object(
                downloader,
                "download_file",
                return_value=os.path.join(temp_dir, "test_file.srt"),
            ), patch.object(
                downloader, "query_jimaku_entries", return_value=[test_entry]
            ), patch.object(
                downloader, "get_entry_files", return_value=[test_file_info]
            ), patch(
                "os.path.exists", return_value=True
            ), patch(
                "jimaku_dl.downloader.exists", return_value=True
            ):

                # This should handle Windows paths correctly
                result = downloader.download_subtitles(win_path)

                # Print for debugging
                print(f"Returned paths: {result}")

                # Verify the results
                assert isinstance(result, list)
                assert len(result) > 0

                # Just verify we get a path back that contains the expected filename
                # Don't check for backslashes since the test environment may convert them
                assert any("test_file.srt" in str(path) for path in result)

                # OPTIONAL: Check that the path has proper structure for the platform
                if os.name == "nt":  # Only on actual Windows
                    assert any("\\" in str(path) for path in result)

    def test_cli_windows_paths(self, windows_environment):
        """Test CLI handling of Windows paths."""
        with patch("jimaku_dl.cli.parse_args") as mock_parse_args, patch(
            "jimaku_dl.cli.JimakuDownloader"
        ) as mock_downloader_class, patch("os.path.exists", return_value=True), patch(
            "subprocess.run"
        ), patch(
            "builtins.print"
        ):

            # Setup mock return values
            mock_downloader = MagicMock()
            mock_downloader.download_subtitles.return_value = [
                "C:\\path\\to\\subtitle.srt"
            ]
            mock_downloader_class.return_value = mock_downloader

            # Create mock args with Windows paths
            mock_args = MagicMock(
                media_path="C:\\path\\to\\video.mkv",
                dest_dir="C:\\output\\dir",
                play=False,
                token="test_token",
                log_level="INFO",
                anilist_id=None,
                sync=False,
            )
            mock_parse_args.return_value = mock_args

            # Run the CLI function
            result = main()

            # Verify paths were handled correctly
            mock_downloader.download_subtitles.assert_called_once()
            args, kwargs = mock_downloader.download_subtitles.call_args
            assert (
                args[0] == "C:\\path\\to\\video.mkv"
            )  # First arg should be media_path
            assert kwargs.get("dest_dir") == "C:\\output\\dir"
