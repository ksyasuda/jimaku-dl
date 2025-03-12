"""
Compatibility module for cross-platform functionality.
"""

import os
import platform
import socket
from typing import Tuple, Union


def is_windows() -> bool:
    """Check if the platform is Windows."""
    env_platform = os.environ.get("PLATFORM_SYSTEM")
    if env_platform:
        return env_platform == "Windows"
    return platform.system() == "Windows"


def is_macos() -> bool:
    """Check if the platform is macOS."""
    env_platform = os.environ.get("PLATFORM_SYSTEM")
    if env_platform:
        return env_platform == "Darwin"
    return platform.system() == "Darwin"


def get_socket_type() -> Tuple[int, int]:
    """
    Return the appropriate socket family and type for the current platform.

    Returns:
        tuple: (family, type) socket constants
    """
    if is_windows():
        return (socket.AF_INET, socket.SOCK_STREAM)
    return (getattr(socket, "AF_UNIX", socket.AF_INET), socket.SOCK_STREAM)


def get_socket_path(socket_name: str) -> Union[str, Tuple[str, int]]:
    """
    Get the appropriate socket path based on the platform.

    Args:
        socket_name: Base name of the socket

    Returns:
        str or tuple: Path for Unix socket or (host, port) for Windows
    """
    if is_windows():
        # On Windows, we use a TCP socket instead of a Unix domain socket
        return ("127.0.0.1", 9001)  # Use localhost and a fixed port

    # On Unix, use the provided socket path
    return socket_name


def connect_socket(
    sock: socket.socket, path_or_addr: Union[str, Tuple[str, int]]
) -> None:
    """
    Connect a socket in a platform-independent way.

    Args:
        sock: Socket object to connect
        path_or_addr: Unix socket path or (host, port) tuple for Windows
    """
    sock.connect(path_or_addr)


def create_mpv_socket_args() -> list:
    """
    Create platform-specific arguments for MPV's socket.

    Returns:
        list: Command line arguments for MPV
    """
    if is_windows():
        return ["--input-ipc-server=tcp://127.0.0.1:9001"]
    return ["--input-ipc-server=/tmp/mpvsocket"]


def normalize_path_for_platform(path: str) -> str:
    """
    Normalize a path for the current platform.

    Args:
        path: Path to normalize

    Returns:
        str: Normalized path
    """
    if is_windows() and "/" in path:
        # More robust implementation for Windows paths
        if path.startswith("/"):
            # Handle absolute paths
            normalized = os.path.normpath(path.replace("/", os.sep))
            # Add a drive letter if it's an absolute path without one
            if not normalized.startswith("\\\\") and not normalized[1:2] == ":":
                normalized = "C:" + normalized
            return normalized
        else:
            # Handle relative paths
            return path.replace("/", os.sep)
    return path


def windows_socket_compat():
    """
    Add necessary compatibility for socket operations on Windows.

    Fixes issues where Windows systems don't have AF_UNIX socket support.
    """
    if is_windows():
        if not hasattr(socket, "AF_UNIX"):
            # Define dummy AF_UNIX for Windows
            socket.AF_UNIX = 1
            # Override connect functions that use AF_UNIX
            old_socket = socket.socket

            def socket_wrapper(*args, **kwargs):
                # Replace AF_UNIX with AF_INET
                if args and args[0] == socket.AF_UNIX:
                    return old_socket(socket.AF_INET, *args[1:], **kwargs)
                return old_socket(*args, **kwargs)

            # Apply the override
            socket.socket = socket_wrapper


def fix_path_separator(path: str) -> str:
    """
    Convert between Unix and Windows path separators as needed.

    Args:
        path: The path to convert

    Returns:
        str: Path with appropriate separators for the current platform
    """
    if is_windows():
        return path.replace("/", "\\")
    else:
        return path.replace("\\", "/")


def get_temp_directory() -> str:
    """
    Get a platform-appropriate temporary directory path.

    Returns:
        str: Path to a writable temp directory
    """
    if is_windows():
        return os.environ.get("TEMP", "C:\\Windows\\Temp")
    return "/tmp"
