#!/usr/bin/env python3
"""Command-line interface for Jimaku Downloader."""

from argparse import ArgumentParser
from os import environ
from sys import exit as sysexit

from jimaku_dl.downloader import JimakuDownloader


def main():
    """
    Command line entry point for Jimaku subtitle downloader.
    """
    parser = ArgumentParser(
        description="Download anime subtitles from Jimaku using the AniList API."
    )
    parser.add_argument("media_path", help="Path to the media file or directory")
    parser.add_argument(
        "--dest",
        help="Directory to save downloaded subtitles (default: same directory as video/input directory)",
    )
    parser.add_argument(
        "--play", action="store_true", help="Launch MPV with the subtitle(s) loaded"
    )
    parser.add_argument(
        "--api-token",
        default=environ.get("JIMAKU_API_TOKEN", ""),
        help="Jimaku API token (or set JIMAKU_API_TOKEN env var)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)",
    )
    args = parser.parse_args()

    try:
        downloader = JimakuDownloader(
            api_token=args.api_token, log_level=args.log_level
        )

        downloaded_files = downloader.download_subtitles(
            media_path=args.media_path, dest_dir=args.dest, play=args.play
        )

        if not downloaded_files:
            print("No subtitle files were downloaded.")
            return 1

        print(f"Successfully downloaded {len(downloaded_files)} subtitle files.")
        return 0

    except ValueError as e:
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sysexit(main())
