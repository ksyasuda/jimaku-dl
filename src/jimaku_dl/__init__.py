"""
Jimaku-dl - A tool for downloading and synchronizing anime subtitles from Jimaku.cc.
"""

__version__ = "0.1.0"  # Set the appropriate version number here

from .downloader import JimakuDownloader

__all__ = ["JimakuDownloader"]
