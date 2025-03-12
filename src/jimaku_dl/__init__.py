"""Jimaku downloader package."""

from jimaku_dl.compat import windows_socket_compat

from .downloader import JimakuDownloader

# Apply Windows socket compatibility early
windows_socket_compat()

__version__ = "0.1.3"  # Updated for socket compatibility fixes

__all__ = ["JimakuDownloader"]
