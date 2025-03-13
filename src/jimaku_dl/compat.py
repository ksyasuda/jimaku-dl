"""Platform compatibility module for jimaku-dl.

This module provides platform-specific implementations and utilities
to ensure jimaku-dl works consistently across different operating systems.
"""

import os
import platform
import socket
from typing import List, Tuple, Union


def is_windows():
    """Check if the current platform is Windows."""
    return platform.system().lower() == "windows"


def get_appdata_dir():
    """Get the appropriate application data directory for the current platform."""
    if is_windows():
        return os.path.join(os.environ.get("APPDATA", ""), "jimaku-dl")

    # On Unix-like systems (Linux, macOS)
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return os.path.join(xdg_config, "jimaku-dl")
    else:
        return os.path.join(os.path.expanduser("~"), ".config", "jimaku-dl")


def get_socket_type() -> Tuple[int, int]:
    """Get the appropriate socket type for the current platform.

    Returns:
        Tuple[int, int]: Socket family and type constants
            On Windows: (AF_INET, SOCK_STREAM) for TCP/IP sockets
            On Unix: (AF_UNIX, SOCK_STREAM) for Unix domain sockets
    """
    if is_windows():
        return (socket.AF_INET, socket.SOCK_STREAM)
    else:
        return (socket.AF_UNIX, socket.SOCK_STREAM)


def get_socket_path(
    default_path: str = "/tmp/mpvsocket",
) -> Union[str, Tuple[str, int]]:
    """Get the appropriate socket path for the current platform.

    Args:
        default_path: Default socket path (used on Unix systems)

    Returns:
        Union[str, Tuple[str, int]]:
            On Windows: A tuple of (host, port) for TCP socket
            On Unix: A string path to the Unix domain socket
    """
    if is_windows():
        # On Windows, return TCP socket address (localhost, port)
        return ("127.0.0.1", 9001)
    else:
        # On Unix, use the provided path or default
        return default_path


def create_mpv_socket_args() -> List[str]:
    """Create the appropriate socket-related cli args for MPV.

    Returns:
        List[str]: List of command-line arguments to configure MPV's socket interface
    """
    if is_windows():
        # Windows uses TCP sockets
        return ["--input-ipc-server=tcp://127.0.0.1:9001"]
    else:
        # Unix uses domain sockets
        return [f"--input-ipc-server={get_socket_path()}"]


def connect_socket(sock, address):
    """Connect a socket to the given address, with platform-specific handling.

    Args:
        sock: Socket object
        address: Address to connect to (string path or tuple of host/port)

    Returns:
        bool: True if connection succeeded, False otherwise
    """
    try:
        sock.connect(address)
        return True
    except (socket.error, OSError):
        return False


def get_config_path():
    """Get the path to the config file."""
    return os.path.join(get_appdata_dir(), "config.json")


def ensure_dir_exists(directory):
    """Ensure the specified directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def get_executable_name(base_name):
    """Get the platform-specific executable name."""
    return f"{base_name}.exe" if is_windows() else base_name


def normalize_path_for_platform(path):
    """Normalize a path for the current platform.

    This function converts path separators to the format appropriate for the
    current operating system and adds drive letter on Windows if missing.

    Args:
        path: The path to normalize

    Returns:
        str: Path with normalized separators for the current platform
    """
    if is_windows():
        # Replace forward slashes with backslashes for Windows
        normalized = path.replace("/", "\\")

        # Add drive letter only for absolute paths that don't already have one
        if (
            normalized.startswith("\\")
            and not normalized.startswith("\\\\")
            and not normalized[1:2] == ":"
        ):
            normalized = "C:" + normalized

        return normalized
    else:
        # Replace backslashes with forward slashes for Unix-like systems
        return path.replace("\\", "/")


def windows_socket_compat():
    """Apply Windows socket compatibility fixes.

    This is a no-op on non-Windows platforms.
    """
    if not is_windows():
        return

    # Windows compatibility for socket connections
    # This helps with MPV socket communication on Windows
    if not hasattr(socket, "AF_UNIX"):
        socket.AF_UNIX = 1
    if not hasattr(socket, "SOCK_STREAM"):
        socket.SOCK_STREAM = 1
