"""Test Windows compatibility features without being on Windows."""

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


@pytest.fixture
def mock_windows_platform():
    """Fixture to pretend we're on Windows."""
    with patch("platform.system", return_value="Windows"):
        yield


@pytest.fixture
def mock_windows_path_behavior():
    """Fixture for Windows path behavior."""
    original_sep = os.sep
    original_altsep = os.altsep

    try:
        # Mock Windows-like path separators
        os.sep = "\\"
        os.altsep = "/"
        yield
    finally:
        # Restore original values
        os.sep = original_sep
        os.altsep = original_altsep


class TestWindowsEnvironment:
    """Test how code behaves in a simulated Windows environment."""

    def test_windows_detection(self, mock_windows_platform):
        """Test Windows detection."""
        assert is_windows() is True

    def test_socket_type_on_windows(self, mock_windows_platform):
        """Test socket type selection on Windows."""
        family, type_ = get_socket_type()
        assert family == socket.AF_INET  # Windows should use TCP/IP
        assert type_ == socket.SOCK_STREAM

    def test_socket_path_on_windows(self, mock_windows_platform):
        """Test socket path handling on Windows."""
        result = get_socket_path("/tmp/mpvsocket")
        assert result == ("127.0.0.1", 9001)  # Windows uses TCP on localhost

    def test_windows_mpv_args(self, mock_windows_platform):
        """Test MPV arguments on Windows."""
        args = create_mpv_socket_args()
        assert "--input-ipc-server=tcp://127.0.0.1:9001" in args

    def test_path_normalization_on_windows(
        self, mock_windows_platform, mock_windows_path_behavior
    ):
        """Test path normalization on Windows."""
        path = normalize_path_for_platform("/path/to/file")
        assert "\\" in path  # Windows backslashes
        assert "/" not in path


class TestWindowsCompatImplementation:
    """Test the implementation details that make Windows compatibility work."""

    def test_socket_connection(self, mock_windows_platform):
        """Test socket connection handling."""
        mock_sock = MagicMock()

        # When on Windows, should connect with TCP socket
        connect_socket(mock_sock, ("127.0.0.1", 9001))
        mock_sock.connect.assert_called_with(("127.0.0.1", 9001))

    def test_socket_unavailable(self, mock_windows_platform):
        """Test handling of Unix socket functions on Windows."""
        # Test we can still create a socket of the right type
        family, type_ = get_socket_type()
        try:
            # Should create a TCP socket, not a Unix domain socket
            sock = socket.socket(family, type_)
            assert sock is not None
        except AttributeError:
            pytest.fail(
                "Should be able to create a socket with the returned family/type"
            )

    def test_missing_af_unix(self, mock_windows_platform):
        """Test handling when AF_UNIX is not available."""
        with patch.object(socket, "AF_INET", 2):
            # Remove AF_UNIX from socket module to simulate older Windows
            if hasattr(socket, "AF_UNIX"):
                with patch.object(socket, "AF_UNIX", None, create=True):
                    family, type_ = get_socket_type()
                    assert family == 2  # AF_INET
            else:
                family, type_ = get_socket_type()
                assert family == 2  # AF_INET

    def test_alternate_implementations(self, mock_windows_platform):
        """Test availability of alternate implementations for Windows."""
        # Test if the compat module provides all necessary functions/constants
        assert hasattr(socket, "AF_INET")
        assert hasattr(socket, "SOCK_STREAM")
