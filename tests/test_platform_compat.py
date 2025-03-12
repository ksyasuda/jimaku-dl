"""Tests for platform compatibility module."""

import os
import platform
import socket
from unittest.mock import patch, MagicMock

import pytest

from jimaku_dl.compat import (
    is_windows,
    get_socket_type,
    get_socket_path,
    connect_socket,
    create_mpv_socket_args,
    normalize_path_for_platform,
)


class TestPlatformCompat:
    """Tests for platform compatibility functions."""

    def test_is_windows(self):
        """Test is_windows function."""
        with patch("platform.system", return_value="Windows"):
            assert is_windows() is True

        with patch("platform.system", return_value="Linux"):
            assert is_windows() is False

    def test_get_socket_type(self):
        """Test get_socket_type function."""
        with patch("platform.system", return_value="Windows"):
            family, type_ = get_socket_type()
            assert family == socket.AF_INET
            assert type_ == socket.SOCK_STREAM

        # For Linux testing, we need to make sure socket.AF_UNIX exists
        with patch("platform.system", return_value="Linux"):
            # Add AF_UNIX if it doesn't exist (for Windows)
            if not hasattr(socket, "AF_UNIX"):
                with patch("socket.AF_UNIX", 1, create=True):
                    family, type_ = get_socket_type()
                    assert family == 1  # Mocked AF_UNIX value
                    assert type_ == socket.SOCK_STREAM
            else:
                family, type_ = get_socket_type()
                assert family == socket.AF_UNIX
                assert type_ == socket.SOCK_STREAM

    def test_get_socket_path(self):
        """Test get_socket_path function."""
        with patch("platform.system", return_value="Windows"):
            result = get_socket_path("/tmp/mpvsocket")
            assert result == ("127.0.0.1", 9001)

        with patch("platform.system", return_value="Linux"):
            result = get_socket_path("/tmp/mpvsocket")
            assert result == "/tmp/mpvsocket"

    def test_connect_socket(self):
        """Test connect_socket function."""
        mock_socket = MagicMock()

        # Test with Unix path
        connect_socket(mock_socket, "/tmp/mpvsocket")
        mock_socket.connect.assert_called_once_with("/tmp/mpvsocket")

        # Test with Windows address
        mock_socket.reset_mock()
        connect_socket(mock_socket, ("127.0.0.1", 9001))
        mock_socket.connect.assert_called_once_with(("127.0.0.1", 9001))

    def test_create_mpv_socket_args(self):
        """Test create_mpv_socket_args function."""
        with patch("platform.system", return_value="Windows"):
            args = create_mpv_socket_args()
            assert args == ["--input-ipc-server=tcp://127.0.0.1:9001"]

        with patch("platform.system", return_value="Linux"):
            args = create_mpv_socket_args()
            assert args == ["--input-ipc-server=/tmp/mpvsocket"]

    def test_normalize_path_for_platform(self):
        """Test normalize_path_for_platform function."""
        with patch("platform.system", return_value="Windows"):
            # Need to also mock the os.sep to be Windows-style for tests
            with patch("os.sep", "\\"):
                path = normalize_path_for_platform("/path/to/file")
                assert "\\" in path  # Windows backslashes
                assert "/" not in path  # No forward slashes
                assert path == "C:\\path\\to\\file"  # Should add C: for absolute paths

                # Test relative path
                rel_path = normalize_path_for_platform("path/to/file")
                assert rel_path == "path\\to\\file"

        with patch("platform.system", return_value="Linux"):
            path = normalize_path_for_platform("/path/to/file")
            assert path == "/path/to/file"
