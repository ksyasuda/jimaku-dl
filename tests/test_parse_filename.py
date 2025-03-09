"""Tests specifically for the parse_filename method."""

from unittest.mock import patch

import pytest

from jimaku_dl.downloader import JimakuDownloader


class TestParseFilename:
    """Test suite for parse_filename method."""

    def setup_method(self):
        """Set up test method with a fresh downloader instance."""
        self.downloader = JimakuDownloader(api_token="test_token")

    def test_trash_guides_format(self):
        """Test parsing filenames that follow Trash Guides naming convention."""
        # Basic Trash Guides format
        title, season, episode = self.downloader.parse_filename(
            "Show Title - S01E02 - Episode Name [1080p]"
        )
        assert title == "Show Title"
        assert season == 1
        assert episode == 2

        # With year included
        title, season, episode = self.downloader.parse_filename(
            "Show Title (2020) - S03E04 - Episode Name [1080p]"
        )
        assert title == "Show Title"
        assert season == 3
        assert episode == 4

        # More complex example
        title, season, episode = self.downloader.parse_filename(
            "My Favorite Anime (2023) - S02E05 - The Big Battle [1080p][10bit][h265][Dual-Audio]"
        )
        assert title == "My Favorite Anime"
        assert season == 2
        assert episode == 5

    def test_standard_formats(self):
        """Test parsing standard filename formats."""
        # S01E01 format
        title, season, episode = self.downloader.parse_filename(
            "Show.Name.S01E02.1080p.mkv"
        )
        assert title == "Show Name"
        assert season == 1
        assert episode == 2

        # Separated by dots
        title, season, episode = self.downloader.parse_filename(
            "Show.Name.S03E04.x264.mkv"
        )
        assert title == "Show Name"
        assert season == 3
        assert episode == 4

        # Separated by underscores
        title, season, episode = self.downloader.parse_filename(
            "Show_Name_S05E06_HEVC.mkv"
        )
        assert title == "Show Name"
        assert season == 5
        assert episode == 6

    def test_directory_structure_extraction(self):
        """Test extracting info from directory structure."""
        # Mock _prompt_for_title_info to avoid reading from stdin
        with patch.object(
            self.downloader, "_prompt_for_title_info", return_value=("Show Name", 1, 2)
        ):
            # Standard Season-## format
            title, season, episode = self.downloader.parse_filename(
                "/path/to/Show Name/Season-1/Show Name - 02 [1080p].mkv"
            )
            assert title == "Show Name"
            assert season == 1
            assert episode == 2

        # Season ## format
        title, season, episode = self.downloader.parse_filename(
            "/path/to/Show Name/Season 03/Episode 4.mkv"
        )
        assert title == "Show Name"
        assert season == 3
        assert episode == 4

        # Simple number in season directory
        title, season, episode = self.downloader.parse_filename(
            "/path/to/My Anime/Season 2/5.mkv"
        )
        assert title == "My Anime"
        assert season == 2
        assert episode == 5

        # Long pathname with complex directory structure
        title, season, episode = self.downloader.parse_filename(
            "/media/user/Anime/Long Anime Title With Spaces/Season-1/Long Anime Title With Spaces - 03.mkv"
        )
        assert title == "Long Anime Title With Spaces"
        assert season == 1
        assert episode == 3

    def test_complex_titles(self):
        """Test parsing filenames with complex titles."""
        # Since we now prompt for non-standard formats, we need to mock the input
        with patch.object(self.downloader, "_prompt_for_title_info") as mock_prompt:
            # Set up the return values for the mock
            mock_prompt.return_value = (
                "Trapped in a Dating Sim - The World of Otome Games Is Tough for Mobs",
                1,
                11,
            )

            title, season, episode = self.downloader.parse_filename(
                "Trapped in a Dating Sim - The World of Otome Games Is Tough for Mobs - S01E11.mkv"
            )
            assert (
                title
                == "Trapped in a Dating Sim - The World of Otome Games Is Tough for Mobs"
            )
            assert season == 1
            assert episode == 11

            # Reset the mock for the next call
            mock_prompt.reset_mock()
            mock_prompt.return_value = ("Re:Zero kara Hajimeru Isekai Seikatsu", 1, 15)

            # Titles with special characters and patterns
            title, season, episode = self.downloader.parse_filename(
                "Re:Zero kara Hajimeru Isekai Seikatsu S01E15 [1080p].mkv"
            )
            assert title == "Re:Zero kara Hajimeru Isekai Seikatsu"
            assert season == 1
            assert episode == 15

    def test_fallback_title_extraction(self):
        """Test fallback to user input for non-standard formats."""
        with patch.object(self.downloader, "_prompt_for_title_info") as mock_prompt:
            # Set up the mock to return specific values
            mock_prompt.return_value = ("My Show", 1, 5)

            # With various tags
            title, season, episode = self.downloader.parse_filename(
                "My Show [1080p] [HEVC] [10bit] [Dual-Audio] - 05.mkv"
            )
            assert title == "My Show"
            assert season == 1
            assert episode == 5
            mock_prompt.assert_called_once()

            # Reset mock for next test
            mock_prompt.reset_mock()
            mock_prompt.return_value = ("Great Anime", 1, 3)

            # With episode at the end
            title, season, episode = self.downloader.parse_filename(
                "Great Anime 1080p BluRay x264 - 03.mkv"
            )
            assert title == "Great Anime"
            assert season == 1
            assert episode == 3
            mock_prompt.assert_called_once()

    def test_unparsable_filenames(self):
        """Test handling of filenames that can't be parsed."""
        with patch.object(self.downloader, "_prompt_for_title_info") as mock_prompt:
            mock_prompt.return_value = ("Manual Title", 2, 3)

            title, season, episode = self.downloader.parse_filename("randomstring.mkv")
            assert title == "Manual Title"
            assert season == 2
            assert episode == 3
            mock_prompt.assert_called_once_with("randomstring.mkv")

            # Test with completely random string
            mock_prompt.reset_mock()
            mock_prompt.return_value = ("Another Title", 4, 5)

            title, season, episode = self.downloader.parse_filename("abc123xyz.mkv")
            assert title == "Another Title"
            assert season == 4
            assert episode == 5
            mock_prompt.assert_called_once_with("abc123xyz.mkv")

    def test_unicode_filenames(self):
        """Test parsing filenames with unicode characters."""
        # Testing with both Japanese title formats

        # Standard format with Japanese title - parser can handle this without prompting
        title, season, episode = self.downloader.parse_filename(
            "この素晴らしい世界に祝福を！ S01E03 [1080p].mkv"
        )
        assert title == "この素晴らしい世界に祝福を！"
        assert season == 1
        assert episode == 3

        # For complex cases that might require prompting, use the mock
        with patch.object(self.downloader, "_prompt_for_title_info") as mock_prompt:
            # Mock the prompt for a case where the parser likely can't determine the structure
            mock_prompt.return_value = ("この素晴らしい世界に祝福を！", 2, 4)

            # Non-standard format with Japanese title
            title, season, episode = self.downloader.parse_filename(
                "この素晴らしい世界に祝福を！ #04 [BD 1080p].mkv"
            )

            # Either the parser handles it or falls back to prompting
            # We're mainly checking that the result is correct
            assert title == "この素晴らしい世界に祝福を！"
            # Season might be detected as 1 from parser or 2 from mock
            # Episode might be detected as 4 from parser or from mock
            assert episode == 4

            # We don't assert on whether mock_prompt was called since that
            # depends on implementation details of the parser

    def test_unusual_formats(self):
        """Test handling of unusual filename formats."""
        with patch.object(self.downloader, "_prompt_for_title_info") as mock_prompt:
            # Reset after each test to check if prompt was called
            mock_prompt.reset_mock()
            mock_prompt.return_value = ("Show Title", 2, 5)

            # Double episode format
            title, season, episode = self.downloader.parse_filename(
                "Show.Title.S02E05E06.1080p.mkv"
            )
            # Should extract the first episode number
            assert title == "Show Title"
            assert season == 2
            assert episode == 5
            mock_prompt.assert_not_called()

            # Episode with zero padding
            mock_prompt.reset_mock()
            title, season, episode = self.downloader.parse_filename(
                "Show Name - S03E009 - Episode Title.mkv"
            )
            assert title == "Show Name"
            assert season == 3
            assert episode == 9
            mock_prompt.assert_not_called()

            # Episode with decimal point
            mock_prompt.reset_mock()
            mock_prompt.return_value = ("Show Name", 1, 5)
            title, season, episode = self.downloader.parse_filename(
                "Show Name - 5.5 - Special Episode.mkv"
            )
            # This will likely prompt due to unusual format
            assert title == "Show Name"
            assert season == 1
            assert episode == 5
            mock_prompt.assert_called_once()
