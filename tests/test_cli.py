"""Tests for the command line interface module."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from jimaku_dl.cli import __version__, main


class TestCli:
    """Tests for the command line interface."""

    def test_main_success(self, monkeypatch):
        """Test successful execution of the CLI main function."""
        mock_downloader = MagicMock()
        mock_downloader.return_value.download_subtitles.return_value = [
            "/path/to/subtitle.srt"
        ]
        monkeypatch.setattr("jimaku_dl.cli.JimakuDownloader", mock_downloader)

        with patch("sys.argv", ["jimaku-dl", "/path/to/video.mkv"]):
            with patch("jimaku_dl.cli.ArgumentParser.parse_args") as mock_args:
                mock_args.return_value.media_path = "/path/to/video.mkv"
                mock_args.return_value.dest = None
                mock_args.return_value.play = False
                mock_args.return_value.api_token = "test_token"
                mock_args.return_value.log_level = "INFO"
                mock_args.return_value.anilist_id = None

                result = main()

                assert result == 0

                mock_downloader.assert_called_once_with(
                    api_token="test_token", log_level="INFO"
                )
                mock_downloader.return_value.download_subtitles.assert_called_once_with(
                    media_path="/path/to/video.mkv",
                    dest_dir=None,
                    play=False,
                    anilist_id=None,
                )

    def test_main_error(self, monkeypatch):
        """Test CLI error handling."""
        mock_downloader = MagicMock()
        mock_downloader.return_value.download_subtitles.side_effect = ValueError(
            "Test error"
        )
        monkeypatch.setattr("jimaku_dl.cli.JimakuDownloader", mock_downloader)

        with patch("sys.argv", ["jimaku-dl", "/path/to/video.mkv"]):
            with patch("jimaku_dl.cli.ArgumentParser.parse_args") as mock_args:
                mock_args.return_value.media_path = "/path/to/video.mkv"
                mock_args.return_value.dest = None
                mock_args.return_value.play = False
                mock_args.return_value.api_token = "test_token"
                mock_args.return_value.log_level = "INFO"
                mock_args.return_value.anilist_id = None

                with patch("builtins.print") as mock_print:
                    result = main()

                    assert result == 1

                    mock_print.assert_called_with("Error: Test error")

    def test_main_unexpected_error(self, monkeypatch):
        """Test CLI handling of unexpected errors."""
        mock_downloader = MagicMock()
        mock_downloader.return_value.download_subtitles.side_effect = Exception(
            "Unexpected error"
        )
        monkeypatch.setattr("jimaku_dl.cli.JimakuDownloader", mock_downloader)

        with patch("sys.argv", ["jimaku-dl", "/path/to/video.mkv"]):
            with patch("jimaku_dl.cli.ArgumentParser.parse_args") as mock_args:
                mock_args.return_value.media_path = "/path/to/video.mkv"
                mock_args.return_value.dest = None
                mock_args.return_value.play = False
                mock_args.return_value.api_token = "test_token"
                mock_args.return_value.log_level = "INFO"
                mock_args.return_value.anilist_id = None

                with patch("builtins.print") as mock_print:
                    result = main()

                    assert result == 1
                    mock_print.assert_called_with("Unexpected error: Unexpected error")

    def test_anilist_id_arg(self, monkeypatch):
        """Test CLI with anilist_id argument."""
        mock_downloader = MagicMock()
        mock_downloader.return_value.download_subtitles.return_value = [
            "/path/to/subtitle.srt"
        ]
        monkeypatch.setattr("jimaku_dl.cli.JimakuDownloader", mock_downloader)

        with patch(
            "sys.argv", ["jimaku-dl", "/path/to/video.mkv", "--anilist-id", "123456"]
        ):
            with patch("jimaku_dl.cli.ArgumentParser.parse_args") as mock_args:
                mock_args.return_value.media_path = "/path/to/video.mkv"
                mock_args.return_value.dest = None
                mock_args.return_value.play = False
                mock_args.return_value.api_token = "test_token"
                mock_args.return_value.log_level = "INFO"
                mock_args.return_value.anilist_id = 123456

                result = main()

                assert result == 0

                mock_downloader.return_value.download_subtitles.assert_called_once_with(
                    media_path="/path/to/video.mkv",
                    dest_dir=None,
                    play=False,
                    anilist_id=123456,
                )

    def test_dest_arg(self, monkeypatch):
        """Test CLI with dest argument."""
        mock_downloader = MagicMock()
        mock_downloader.return_value.download_subtitles.return_value = [
            "/custom/path/subtitle.srt"
        ]
        monkeypatch.setattr("jimaku_dl.cli.JimakuDownloader", mock_downloader)

        with patch(
            "sys.argv", ["jimaku-dl", "/path/to/video.mkv", "--dest", "/custom/path"]
        ):
            with patch("jimaku_dl.cli.ArgumentParser.parse_args") as mock_args:
                mock_args.return_value.media_path = "/path/to/video.mkv"
                mock_args.return_value.dest = "/custom/path"
                mock_args.return_value.play = False
                mock_args.return_value.api_token = "test_token"
                mock_args.return_value.log_level = "INFO"
                mock_args.return_value.anilist_id = None

                result = main()

                assert result == 0
                mock_downloader.return_value.download_subtitles.assert_called_once_with(
                    media_path="/path/to/video.mkv",
                    dest_dir="/custom/path",
                    play=False,
                    anilist_id=None,
                )

    def test_play_arg(self, monkeypatch):
        """Test CLI with play argument."""
        mock_downloader = MagicMock()
        mock_downloader.return_value.download_subtitles.return_value = [
            "/path/to/subtitle.srt"
        ]
        monkeypatch.setattr("jimaku_dl.cli.JimakuDownloader", mock_downloader)

        with patch("sys.argv", ["jimaku-dl", "/path/to/video.mkv", "--play"]):
            with patch("jimaku_dl.cli.ArgumentParser.parse_args") as mock_args:
                mock_args.return_value.media_path = "/path/to/video.mkv"
                mock_args.return_value.dest = None
                mock_args.return_value.play = True
                mock_args.return_value.api_token = "test_token"
                mock_args.return_value.log_level = "INFO"
                mock_args.return_value.anilist_id = None

                result = main()

                assert result == 0
                mock_downloader.return_value.download_subtitles.assert_called_once_with(
                    media_path="/path/to/video.mkv",
                    dest_dir=None,
                    play=True,
                    anilist_id=None,
                )

    def test_token_arg(self, monkeypatch):
        """Test CLI with token argument."""
        mock_downloader = MagicMock()
        mock_downloader.return_value.download_subtitles.return_value = [
            "/path/to/subtitle.srt"
        ]
        monkeypatch.setattr("jimaku_dl.cli.JimakuDownloader", mock_downloader)

        with patch(
            "sys.argv", ["jimaku-dl", "/path/to/video.mkv", "--token", "custom_token"]
        ):
            with patch("jimaku_dl.cli.ArgumentParser.parse_args") as mock_args:
                mock_args.return_value.media_path = "/path/to/video.mkv"
                mock_args.return_value.dest = None
                mock_args.return_value.play = False
                mock_args.return_value.api_token = "custom_token"
                mock_args.return_value.log_level = "INFO"
                mock_args.return_value.anilist_id = None

                result = main()

                assert result == 0
                mock_downloader.assert_called_once_with(
                    api_token="custom_token", log_level="INFO"
                )

    def test_log_level_arg(self, monkeypatch):
        """Test CLI with log_level argument."""
        mock_downloader = MagicMock()
        mock_downloader.return_value.download_subtitles.return_value = [
            "/path/to/subtitle.srt"
        ]
        monkeypatch.setattr("jimaku_dl.cli.JimakuDownloader", mock_downloader)

        with patch(
            "sys.argv", ["jimaku-dl", "/path/to/video.mkv", "--log-level", "DEBUG"]
        ):
            with patch("jimaku_dl.cli.ArgumentParser.parse_args") as mock_args:
                mock_args.return_value.media_path = "/path/to/video.mkv"
                mock_args.return_value.dest = None
                mock_args.return_value.play = False
                mock_args.return_value.api_token = "test_token"
                mock_args.return_value.log_level = "DEBUG"
                mock_args.return_value.anilist_id = None

                result = main()

                assert result == 0
                mock_downloader.assert_called_once_with(
                    api_token="test_token", log_level="DEBUG"
                )

    def test_version_arg(self, capsys, monkeypatch):
        """Test CLI with version argument."""
        with patch("sys.argv", ["jimaku-dl", "--version"]):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0

            # Check that version is printed
            captured = capsys.readouterr()
            assert f"jimaku-dl {__version__}" in captured.out

    def test_help_arg(self, capsys, monkeypatch):
        """Test CLI with help argument."""
        with patch("sys.argv", ["jimaku-dl", "--help"]):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0

            # Help text is printed to stdout by argparse
            captured = capsys.readouterr()
            assert "usage:" in captured.out

    def test_keyboard_interrupt(self, monkeypatch):
        """Test handling of keyboard interrupt."""
        mock_downloader = MagicMock()
        mock_downloader.return_value.download_subtitles.side_effect = (
            KeyboardInterrupt()
        )
        monkeypatch.setattr("jimaku_dl.cli.JimakuDownloader", mock_downloader)

        with patch("sys.argv", ["jimaku-dl", "/path/to/video.mkv"]):
            with patch("jimaku_dl.cli.ArgumentParser.parse_args") as mock_args:
                mock_args.return_value.media_path = "/path/to/video.mkv"
                mock_args.return_value.dest = None
                mock_args.return_value.play = False
                mock_args.return_value.api_token = "test_token"
                mock_args.return_value.log_level = "INFO"
                mock_args.return_value.anilist_id = None

                with patch("builtins.print") as mock_print:
                    result = main()

                    assert result == 1
                    mock_print.assert_called_with("\nOperation cancelled by user.")

    def test_short_options(self, monkeypatch):
        """Test CLI with short options instead of long options."""
        mock_downloader = MagicMock()
        mock_downloader.return_value.download_subtitles.return_value = [
            "/path/to/subtitle.srt"
        ]
        monkeypatch.setattr("jimaku_dl.cli.JimakuDownloader", mock_downloader)

        with patch(
            "sys.argv",
            [
                "jimaku-dl",
                "/path/to/video.mkv",
                "-d",
                "/custom/path",
                "-p",
                "-t",
                "short_token",
                "-l",
                "DEBUG",
                "-a",
                "789",
            ],
        ):
            with patch("jimaku_dl.cli.ArgumentParser.parse_args") as mock_args:
                mock_args.return_value.media_path = "/path/to/video.mkv"
                mock_args.return_value.dest = "/custom/path"
                mock_args.return_value.play = True
                mock_args.return_value.api_token = "short_token"
                mock_args.return_value.log_level = "DEBUG"
                mock_args.return_value.anilist_id = 789

                result = main()

                assert result == 0
                mock_downloader.assert_called_once_with(
                    api_token="short_token", log_level="DEBUG"
                )
                mock_downloader.return_value.download_subtitles.assert_called_once_with(
                    media_path="/path/to/video.mkv",
                    dest_dir="/custom/path",
                    play=True,
                    anilist_id=789,
                )
