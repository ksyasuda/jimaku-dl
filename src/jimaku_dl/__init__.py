"""
Jimaku Downloader - Download anime subtitles from Jimaku using the AniList API.

This package provides functionality to search for, select, and download
subtitles for anime media files or directories.
"""

__version__ = "0.1.0"

from .downloader import JimakuDownloader

__all__ = ["JimakuDownloader"]
