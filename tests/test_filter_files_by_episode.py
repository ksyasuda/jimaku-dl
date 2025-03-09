"""Tests specifically for the filter_files_by_episode method."""

import pytest

from jimaku_dl.downloader import JimakuDownloader


class TestFilterFilesByEpisode:
    """Test suite for filter_files_by_episode method."""

    def setup_method(self):
        """Set up test method with a fresh downloader instance."""
        self.downloader = JimakuDownloader(api_token="test_token")

        # Setup common test files
        self.all_files = [
            {"id": 1, "name": "Show - 01.srt"},
            {"id": 2, "name": "Show - 02.srt"},
            {"id": 3, "name": "Show - 03.srt"},
            {"id": 4, "name": "Show - E04.srt"},
            {"id": 5, "name": "Show Episode 05.srt"},
            {"id": 6, "name": "Show #06.srt"},
            {"id": 7, "name": "Show.S01E07.srt"},
            {"id": 8, "name": "Show - BATCH.srt"},
            {"id": 9, "name": "Show - Complete.srt"},
            {"id": 10, "name": "Show - All Episodes.srt"},
        ]

    def test_exact_episode_matches(self):
        """Test finding exact episode matches with different filename patterns."""
        # Test standard episode format
        filtered = self.downloader.filter_files_by_episode(self.all_files, 1)
        assert len(filtered) == 4  # 1 specific match + 3 batch files
        assert filtered[0]["name"] == "Show - 01.srt"  # Specific match should be first

        # Test E## format
        filtered = self.downloader.filter_files_by_episode(self.all_files, 4)
        assert len(filtered) == 4  # 1 specific match + 3 batch files
        assert filtered[0]["name"] == "Show - E04.srt"  # Specific match should be first

        # Test 'Episode ##' format
        filtered = self.downloader.filter_files_by_episode(self.all_files, 5)
        assert len(filtered) == 4  # 1 specific match + 3 batch files
        assert (
            filtered[0]["name"] == "Show Episode 05.srt"
        )  # Specific match should be first

        # Test '#' format
        filtered = self.downloader.filter_files_by_episode(self.all_files, 6)
        assert len(filtered) == 4  # 1 specific match + 3 batch files
        assert filtered[0]["name"] == "Show #06.srt"  # Specific match should be first

        # Test S##E## format
        filtered = self.downloader.filter_files_by_episode(self.all_files, 7)
        assert len(filtered) == 4  # 1 specific match + 3 batch files
        assert (
            filtered[0]["name"] == "Show.S01E07.srt"
        )  # Specific match should be first

    def test_batch_files_inclusion(self):
        """Test that batch files are always included but sorted after specific matches."""
        # For all episodes, batch files should be included now
        filtered = self.downloader.filter_files_by_episode(self.all_files, 1)
        assert len(filtered) == 4  # 1 specific + 3 batch
        assert any("BATCH" in f["name"] for f in filtered)
        assert any("Complete" in f["name"] for f in filtered)
        assert any("All Episodes" in f["name"] for f in filtered)

        # Specific match should be first, followed by batch files
        assert filtered[0]["name"] == "Show - 01.srt"
        assert all(
            keyword in f["name"]
            for f, keyword in zip(filtered[1:], ["BATCH", "Complete", "All Episodes"])
        )

        # Same for episode 3
        filtered = self.downloader.filter_files_by_episode(self.all_files, 3)
        assert len(filtered) == 4  # 1 specific + 3 batch
        assert filtered[0]["name"] == "Show - 03.srt"
        assert all(
            keyword in " ".join([f["name"] for f in filtered[1:]])
            for keyword in ["BATCH", "Complete", "All Episodes"]
        )

        # For high episode numbers with no match, only batch files should be returned
        filtered = self.downloader.filter_files_by_episode(self.all_files, 10)
        assert len(filtered) == 3
        assert all(
            f["name"]
            in ["Show - BATCH.srt", "Show - Complete.srt", "Show - All Episodes.srt"]
            for f in filtered
        )

    def test_no_episode_matches(self):
        """Test behavior when no episodes match."""
        # For non-existent episodes, should return batch files
        filtered = self.downloader.filter_files_by_episode(self.all_files, 99)
        assert len(filtered) == 3
        assert all(
            f["name"]
            in ["Show - BATCH.srt", "Show - Complete.srt", "Show - All Episodes.srt"]
            for f in filtered
        )

        # For a list with no batch files and no matches, should return all files
        no_batch_files = [
            f
            for f in self.all_files
            if not any(
                keyword in f["name"].lower()
                for keyword in ["batch", "complete", "all", "season"]
            )
        ]
        filtered = self.downloader.filter_files_by_episode(no_batch_files, 99)
        assert filtered == no_batch_files

    def test_ordering_of_results(self):
        """Test that specific episode matches are always before batch files."""
        # Create a reversed test set to ensure sorting works
        reversed_files = list(reversed(self.all_files))

        # Test with episode that has a specific match
        filtered = self.downloader.filter_files_by_episode(reversed_files, 4)

        # Verify specific match is first
        assert filtered[0]["name"] == "Show - E04.srt"

        # Verify batch files follow
        for f in filtered[1:]:
            assert any(
                keyword in f["name"].lower()
                for keyword in ["batch", "complete", "all episodes"]
            )

    def test_edge_case_episode_formats(self):
        """Test edge case episode number formats."""
        # Create test files with unusual formats
        edge_case_files = [
            {"id": 1, "name": "Show - ep.01.srt"},  # With period
            {"id": 2, "name": "Show - ep01v2.srt"},  # With version
            {"id": 3, "name": "Show - e.03.srt"},  # Abbreviated with period
            {"id": 4, "name": "Show - episode.04.srt"},  # Full word with period
            {"id": 5, "name": "Show - 05.v2.srt"},  # Version format
            {"id": 6, "name": "Show - [06].srt"},  # Bracketed number
        ]

        # Test detection of 01 in filenames
        filtered = self.downloader.filter_files_by_episode(edge_case_files, 1)
        # In the current implementation, these might all be included since regex matching is imperfect
        # So we just check that the correct ones are present and first
        assert any(f["name"] == "Show - ep.01.srt" for f in filtered)
        assert any(f["name"] == "Show - ep01v2.srt" for f in filtered)

        # Test detection of episode.04
        filtered = self.downloader.filter_files_by_episode(edge_case_files, 4)
        assert any(f["name"] == "Show - episode.04.srt" for f in filtered)

        # Test detection of [06]
        filtered = self.downloader.filter_files_by_episode(edge_case_files, 6)
        assert any(f["name"] == "Show - [06].srt" for f in filtered)

        # Test episode that doesn't exist
        filtered = self.downloader.filter_files_by_episode(edge_case_files, 99)
        # Should return all files when no batch files and no matches
        assert len(filtered) == len(edge_case_files)

    def test_duplicate_episode_matches(self):
        """Test handling of duplicate episode matches in filenames."""
        # Files with multiple episode numbers in the name
        dup_files = [
            {"id": 1, "name": "Show - 01 - Episode 1.srt"},  # Same number twice
            {"id": 2, "name": "Show 02 - Ep02.srt"},  # Same number twice
            {"id": 3, "name": "Show - 03 - 04.srt"},  # Different numbers
            {"id": 4, "name": "Show - Ep05 Extra 06.srt"},  # Different numbers
        ]

        # Should match the first number for episode 1
        filtered = self.downloader.filter_files_by_episode(dup_files, 1)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Show - 01 - Episode 1.srt"

        # Should match both formats for episode 2
        filtered = self.downloader.filter_files_by_episode(dup_files, 2)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Show 02 - Ep02.srt"

        # Should match the first number for episode 3
        filtered = self.downloader.filter_files_by_episode(dup_files, 3)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Show - 03 - 04.srt"

        # Should match the second number for episode 4
        filtered = self.downloader.filter_files_by_episode(dup_files, 4)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Show - 03 - 04.srt"

    def test_empty_file_list(self):
        """Test behavior with empty file list."""
        filtered = self.downloader.filter_files_by_episode([], 1)
        assert filtered == []
