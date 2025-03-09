"""Tests specifically for the parse_directory_name method."""

import pytest

from jimaku_dl.downloader import JimakuDownloader


class TestParseDirectoryName:
    """Test suite for parse_directory_name method."""

    def setup_method(self):
        """Set up test method with a fresh downloader instance."""
        self.downloader = JimakuDownloader(api_token="test_token")

    def test_basic_directory_names(self):
        """Test basic directory name parsing."""
        # Standard name
        success, title, season, episode = self.downloader.parse_directory_name(
            "/path/to/My Anime Show"
        )
        assert success is True
        assert title == "My Anime Show"
        assert season == 1
        assert episode == 0

        # Name with underscores
        success, title, season, episode = self.downloader.parse_directory_name(
            "/path/to/My_Anime_Show"
        )
        assert success is True
        assert title == "My Anime Show"  # Underscores should be converted to spaces
        assert season == 1
        assert episode == 0

        # Name with dots
        success, title, season, episode = self.downloader.parse_directory_name(
            "/path/to/My.Anime.Show"
        )
        assert success is True
        assert title == "My Anime Show"  # Dots should be converted to spaces
        assert season == 1
        assert episode == 0

    def test_common_system_directories(self):
        """Test handling of common system directories that should be rejected."""
        # Common system directories
        for sys_dir in [
            "bin",
            "etc",
            "lib",
            "home",
            "usr",
            "var",
            "tmp",
            "opt",
            "media",
            "mnt",
        ]:
            success, _, _, _ = self.downloader.parse_directory_name(
                f"/path/to/{sys_dir}"
            )
            assert success is False, f"Directory '{sys_dir}' should be rejected"

        # Root directory
        success, _, _, _ = self.downloader.parse_directory_name("/")
        assert success is False

        # Current directory
        success, _, _, _ = self.downloader.parse_directory_name(".")
        assert success is False

        # Parent directory
        success, _, _, _ = self.downloader.parse_directory_name("..")
        assert success is False

    def test_short_directory_names(self):
        """Test handling of directory names that are too short."""
        # One-character name
        success, _, _, _ = self.downloader.parse_directory_name("/path/to/A")
        assert success is False

        # Two-character name
        success, _, _, _ = self.downloader.parse_directory_name("/path/to/AB")
        assert success is False

        # Three-character name (should be accepted)
        success, title, _, _ = self.downloader.parse_directory_name("/path/to/ABC")
        assert success is True
        assert title == "ABC"

    def test_special_characters(self):
        """Test directories with special characters."""
        # Directory with parentheses
        success, title, _, _ = self.downloader.parse_directory_name(
            "/path/to/My Anime (2022)"
        )
        assert success is True
        assert title == "My Anime (2022)"

        # Directory with brackets
        success, title, _, _ = self.downloader.parse_directory_name(
            "/path/to/My Anime [Uncensored]"
        )
        assert success is True
        assert title == "My Anime [Uncensored]"

        # Directory with other special characters
        success, title, _, _ = self.downloader.parse_directory_name(
            "/path/to/My Anime: The Movie - Part 2!"
        )
        assert success is True
        assert title == "My Anime: The Movie - Part 2!"

    def test_directory_with_season_info(self):
        """Test directories with season information."""
        # Directory with season in name
        success, title, _, _ = self.downloader.parse_directory_name(
            "/path/to/Anime Season 2"
        )
        assert success is True
        assert title == "Anime Season 2"

        # Directory that only specifies season
        success, title, _, _ = self.downloader.parse_directory_name("/path/to/Season 3")
        assert success is True
        assert title == "Season 3"
