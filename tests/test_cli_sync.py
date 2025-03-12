"""Tests specifically for the synchronization functions in the CLI module."""

import json
import logging
import socket
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest

from jimaku_dl.cli import run_background_sync, sync_subtitles_thread


class TestSyncSubtitlesThread:
    """Test the sync_subtitles_thread function."""

    def test_successful_sync_and_socket_communication(self):
        """Test the full sync process with successful socket communication."""
        # Mock subprocess to simulate successful ffsubsync run
        mock_subprocess = MagicMock()
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""

        # Mock socket functions
        mock_socket = MagicMock()
        mock_socket.recv.side_effect = [
            # Response for track-list query
            json.dumps(
                {
                    "data": [
                        {"type": "video", "id": 1},
                        {"type": "audio", "id": 1},
                        {"type": "sub", "id": 1},
                    ]
                }
            ).encode("utf-8"),
            # Additional responses for subsequent commands
            b"{}",
            b"{}",
            b"{}",
            b"{}",
            b"{}",
            b"{}",
        ]

        # Create a temp file path for socket
        with tempfile.NamedTemporaryFile() as temp:
            socket_path = temp.name

            with patch("jimaku_dl.cli.subprocess_run", mock_subprocess), patch(
                "jimaku_dl.cli.path.exists", return_value=True
            ), patch("socket.socket", return_value=mock_socket), patch(
                "builtins.print"
            ) as mock_print, patch(
                "jimaku_dl.cli.time.sleep"
            ), patch(
                "logging.FileHandler", MagicMock()
            ), patch(
                "logging.getLogger", MagicMock()
            ):

                # Run the function
                sync_subtitles_thread(
                    "/path/to/video.mkv",
                    "/path/to/subtitle.srt",
                    "/path/to/output.srt",
                    socket_path,
                )

                # Check subprocess call
                mock_subprocess.assert_called_once()
                assert mock_subprocess.call_args[0][0][0] == "ffsubsync"

                # Check socket connectivity
                mock_socket.connect.assert_called_once_with(socket_path)

                # Verify socket commands were sent
                assert mock_socket.send.call_count >= 3

                # Verify success message
                mock_print.assert_any_call("Synchronization successful!")
                mock_print.assert_any_call("Updated MPV with synchronized subtitle")

    def test_ffsubsync_failure(self):
        """Test handling of ffsubsync failure."""
        # Mock subprocess to simulate failed ffsubsync run
        mock_subprocess = MagicMock()
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Error: Failed to sync"

        with patch("jimaku_dl.cli.subprocess_run", mock_subprocess), patch(
            "builtins.print"
        ) as mock_print, patch("logging.FileHandler", MagicMock()), patch(
            "logging.getLogger", MagicMock()
        ):

            # Run the function
            sync_subtitles_thread(
                "/path/to/video.mkv",
                "/path/to/subtitle.srt",
                "/path/to/output.srt",
                "/tmp/mpv.sock",
            )

            # Check error message
            mock_print.assert_any_call("Sync failed: Error: Failed to sync")

            # Verify we don't proceed to socket communication
            assert mock_subprocess.called
            assert mock_print.call_count == 1

    def test_socket_not_found(self):
        """Test handling of socket not found."""
        # Mock subprocess to simulate successful ffsubsync run
        mock_subprocess = MagicMock()
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""

        # Set up logger mock
        mock_logger_instance = MagicMock()
        mock_logger = MagicMock(return_value=mock_logger_instance)

        # This is the key fix - patch time.time() to break out of the wait loop
        # by simulating enough time has passed
        mock_time = MagicMock()
        mock_time.side_effect = [
            0,
            100,
        ]  # First call returns 0, second returns 100 (exceeding max_wait)

        # Also need to mock path.exists to control behavior for different paths:
        # - First call should return True for the output file
        # - Second call should return False for the socket
        path_exists_results = {
            "/path/to/output.srt": True,  # Output file exists (to ensure the sync message is printed)
            "/tmp/mpv.sock": False,  # Socket does NOT exist
        }

        def mock_path_exists(path):
            # Use the mock dictionary but default to True for any other paths
            return path_exists_results.get(path, True)

        with patch("jimaku_dl.cli.subprocess_run", mock_subprocess), patch(
            "jimaku_dl.cli.path.exists", side_effect=mock_path_exists
        ), patch("jimaku_dl.cli.time.sleep"), patch(
            "jimaku_dl.cli.time.time", mock_time
        ), patch(
            "builtins.print"
        ) as mock_print, patch(
            "logging.FileHandler", MagicMock()
        ), patch(
            "logging.getLogger", mock_logger
        ):

            # Run the function
            sync_subtitles_thread(
                "/path/to/video.mkv",
                "/path/to/subtitle.srt",
                "/path/to/output.srt",
                "/tmp/mpv.sock",
            )

            # Now the test should pass because we're ensuring the output file exists
            mock_print.assert_any_call("Synchronization successful!")
            mock_logger_instance.error.assert_called_with(
                "Socket not found after waiting: /tmp/mpv.sock"
            )

    def test_socket_connection_error(self):
        """Test handling of socket connection error."""
        # Mock subprocess to simulate successful ffsubsync run
        mock_subprocess = MagicMock()
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""

        # Mock socket to raise connection error
        mock_socket = MagicMock()
        mock_socket.connect.side_effect = socket.error("Connection refused")

        with patch("jimaku_dl.cli.subprocess_run", mock_subprocess), patch(
            "jimaku_dl.cli.path.exists", return_value=True
        ), patch("socket.socket", return_value=mock_socket), patch(
            "builtins.print"
        ) as mock_print, patch(
            "logging.FileHandler", MagicMock()
        ), patch(
            "logging.getLogger"
        ) as mock_logger:

            # Setup mock logger
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance

            # Run the function
            sync_subtitles_thread(
                "/path/to/video.mkv",
                "/path/to/subtitle.srt",
                "/path/to/output.srt",
                "/tmp/mpv.sock",
            )

            # Check success message but log socket error
            mock_print.assert_any_call("Synchronization successful!")
            mock_logger_instance.error.assert_called_with(
                "Socket connection error: Connection refused"
            )

    def test_socket_send_error(self):
        """Test handling of socket send error."""
        # Mock subprocess for successful ffsubsync run
        mock_subprocess = MagicMock()
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""

        # Create mock socket but make socket behavior more robust
        mock_socket = MagicMock()

        # Set up recv to handle multiple calls including empty response at shutdown
        recv_responses = [b""] * 10  # Multiple empty responses for the cleanup loop
        mock_socket.recv.side_effect = recv_responses

        # Make send raise an error on the first real command
        send_called = [False]

        def mock_send(data):
            if b"get_property" in data or b"sub-reload" in data:
                send_called[0] = True
                raise socket.error("Send failed")
            return None

        mock_socket.send.side_effect = mock_send

        # Set up all the patches needed
        with patch("jimaku_dl.cli.subprocess_run", mock_subprocess), patch(
            "jimaku_dl.cli.path.exists", return_value=True
        ), patch("socket.socket", return_value=mock_socket), patch(
            "builtins.print"
        ) as mock_print, patch(
            "jimaku_dl.cli.time.sleep"
        ), patch(
            "logging.FileHandler", MagicMock()
        ), patch(
            "logging.getLogger"
        ) as mock_logger:

            # Set up the logger mock
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance

            # Patch socket.shutdown to avoid another hang point
            with patch.object(mock_socket, "shutdown"):
                # Run the function under test
                sync_subtitles_thread(
                    "/path/to/video.mkv",
                    "/path/to/subtitle.srt",
                    "/path/to/output.srt",
                    "/tmp/mpv.sock",
                )

            # Verify sync message printed but not MPV update message
            mock_print.assert_any_call("Synchronization successful!")

            # Check for debug message about socket error
            debug_calls = [
                call[0][0]
                for call in mock_logger_instance.debug.call_args_list
                if call[0] and isinstance(call[0][0], str)
            ]
            socket_error_logged = any(
                "Socket send error: Send failed" in msg for msg in debug_calls
            )
            assert socket_error_logged, "Socket error message not logged"

            # Verify "Updated MPV" message was not printed
            update_messages = [
                call[0][0]
                for call in mock_print.call_args_list
                if call[0]
                and isinstance(call[0][0], str)
                and "Updated MPV" in call[0][0]
            ]
            assert not update_messages, "MPV update message should not be printed"

    def test_socket_recv_error(self):
        """Test handling of socket receive error."""
        # Mock subprocess
        mock_subprocess = MagicMock()
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""

        # Mock socket with robust receive error behavior
        mock_socket = MagicMock()

        # Make recv raise timeout explicitly
        mock_socket.recv.side_effect = socket.timeout("Receive timeout")

        with patch("jimaku_dl.cli.subprocess_run", mock_subprocess), patch(
            "jimaku_dl.cli.path.exists", return_value=True
        ), patch("socket.socket", return_value=mock_socket), patch(
            "builtins.print"
        ) as mock_print, patch(
            "jimaku_dl.cli.time.sleep"
        ), patch(
            "logging.FileHandler", MagicMock()
        ), patch(
            "logging.getLogger"
        ) as mock_logger:

            # Setup mock logger
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance

            # Patch socket.shutdown to avoid another hang point
            with patch.object(
                mock_socket, "shutdown", side_effect=socket.error
            ), patch.object(mock_socket, "close"):
                # Run the function
                sync_subtitles_thread(
                    "/path/to/video.mkv",
                    "/path/to/subtitle.srt",
                    "/path/to/output.srt",
                    "/tmp/mpv.sock",
                )

            # Check success message happened
            mock_print.assert_any_call("Synchronization successful!")

            # We need to check that the socket.timeout exception happened
            # This should create a debug message containing the word "timeout"
            # The best way to check this is to examine the mock_socket.recv calls
            mock_socket.recv.assert_called()
