#!/usr/bin/env python3
from logging import Logger, basicConfig, getLogger
from os import environ
from os.path import abspath, basename, dirname, exists, isdir, join, normpath, splitext
from re import IGNORECASE
from re import compile as re_compile
from re import search, sub
from subprocess import CalledProcessError
from subprocess import run as subprocess_run
from typing import Any, Dict, List, Optional, Tuple, Union

from requests import get as requests_get
from requests import post as requests_post


class JimakuDownloader:
    """
    Main class for downloading subtitles from Jimaku using the AniList API.

    This class provides functionality to search for, select, and download
    subtitles for anime media files or directories.
    """

    ANILIST_API_URL = "https://graphql.anilist.co"
    JIMAKU_SEARCH_URL = "https://jimaku.cc/api/entries/search"
    JIMAKU_FILES_BASE = "https://jimaku.cc/api/entries"

    def __init__(self, api_token: Optional[str] = None, log_level: str = "INFO"):
        """
        Initialize the JimakuDownloader with API token and logging configuration.

        Parameters
        ----------
        api_token : str, optional
            Jimaku API token for authentication. If None, will try to get from JIMAKU_API_TOKEN env var
        log_level : str, default="INFO"
            Logging level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = self._setup_logging(log_level)

        self.api_token = api_token or environ.get("JIMAKU_API_TOKEN", "")
        if not self.api_token:
            self.logger.warning(
                "No API token provided. Will need to be set before downloading."
            )

    def _setup_logging(self, log_level: str) -> Logger:
        """
        Configure logging with the specified level.

        Parameters
        ----------
        log_level : str
            The desired log level (e.g. "INFO", "DEBUG", etc.)

        Returns
        -------
        logger : logging.Logger
            Configured logger instance
        """
        import logging

        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {log_level}")

        basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        return getLogger(__name__)

    def is_directory_input(self, path: str) -> bool:
        """
        Check if the input path is a directory.

        Parameters
        ----------
        path : str
            Path to check

        Returns
        -------
        bool
            True if the path is a directory, False otherwise
        """
        return isdir(path)

    def parse_filename(self, filename: str) -> Tuple[str, int, int]:
        """
        Extract show title, season, and episode number from the filename.

        Parameters
        ----------
        filename : str
            The filename to parse

        Returns
        -------
        tuple
            (title, season, episode) where:
            - title (str): Show title
            - season (int): Season number
            - episode (int): Episode number
        """
        # Clean up filename first to handle parentheses and brackets
        clean_filename = filename

        # Try Trash Guides anime naming schema first
        # Format: {Series Title} - S{season:00}E{episode:00} - {Episode Title} [...]
        trash_guide_match = search(
            r"(.+?)(?:\(\d{4}\))?\s*-\s*[Ss](\d+)[Ee](\d+)\s*-\s*.+",
            basename(clean_filename),
        )
        if trash_guide_match:
            title = trash_guide_match.group(1).strip()
            season = int(trash_guide_match.group(2))
            episode = int(trash_guide_match.group(3))
            self.logger.debug(
                f"Parsed using Trash Guides format: {title=}, {season=}, {episode=}"
            )
            return title, season, episode

        # Try to extract from directory structure following Trash Guides format
        # Format: /path/to/{Series Title}/Season {season}/{filename}
        parts = normpath(clean_filename).split("/")
        if len(parts) >= 3 and "season" in parts[-2].lower():
            # Get season from the Season XX directory
            season_match = search(r"season\s*(\d+)", parts[-2].lower())
            if season_match:
                season = int(season_match.group(1))
                # The show title is likely the directory name one level up
                title = parts[-3]

                # Try to get episode number from filename
                ep_match = search(
                    r"[Ss](\d+)[Ee](\d+)|[Ee](?:pisode)?\s*(\d+)|(?:^|\s|[._-])(\d+)(?:\s|$|[._-])",
                    parts[-1],
                )
                if ep_match:
                    # Find the first non-None group which contains the episode number
                    episode_groups = ep_match.groups()
                    episode_str = next(
                        (g for g in episode_groups if g is not None), "1"
                    )
                    # If we found S01E01 format, use the episode part (second group)
                    if ep_match.group(1) is not None and ep_match.group(2) is not None:
                        episode_str = ep_match.group(2)
                    episode = int(episode_str)
                else:
                    episode = 1

                self.logger.debug(
                    f"Parsed from Trash Guides directory structure: {title=}, {season=}, {episode=}"
                )
                return title, season, episode

        # Try the standard S01E01 format
        match = search(r"(.+?)[. _-]+[Ss](\d+)[Ee](\d+)", clean_filename)
        if match:
            title = match.group(1).replace(".", " ").strip().replace("_", " ")
            season = int(match.group(2))
            episode = int(match.group(3))
            self.logger.debug(
                f"Parsed using S01E01 format: {title=}, {season=}, {episode=}"
            )
            return title, season, episode

        # Try to extract from paths like "Show Name/Season-1/Episode" format
        parts = normpath(filename).split("/")
        if len(parts) >= 3:
            # Check if the parent directory contains "Season" in the name
            season_dir = parts[-2]
            if "season" in season_dir.lower():
                season_match = search(r"season[. _-]*(\d+)", season_dir.lower())
                if season_match:
                    season = int(season_match.group(1))
                    # The show name is likely 2 directories up
                    title = parts[-3].replace(".", " ").strip()
                    # Try to find episode number in the filename
                    ep_match = search(
                        r"[Ee](?:pisode)?[. _-]*(\d+)|[. _-](\d+)[. _-]", parts[-1]
                    )
                    episode = int(
                        ep_match.group(1)
                        if ep_match and ep_match.group(1)
                        else ep_match.group(2) if ep_match and ep_match.group(2) else 1
                    )
                    self.logger.debug(
                        f"Parsed from directory structure: {title=}, {season=}, {episode=}"
                    )
                    return title, season, episode

        return self._prompt_for_title_info(filename)

    def _prompt_for_title_info(self, filename: str) -> Tuple[str, int, int]:
        """
        Prompt the user to manually enter show title and episode info.
        """
        self.logger.warning("Could not parse filename automatically.")
        print(f"\nFilename: {filename}")
        print("Could not automatically determine anime title and episode information.")
        title = input("Please enter the anime title: ").strip()
        try:
            season = int(
                input("Enter season number (or 0 if not applicable): ").strip() or "1"
            )
            episode = int(
                input("Enter episode number (or 0 if not applicable): ").strip() or "1"
            )
        except ValueError:
            self.logger.error("Invalid input.")
            raise ValueError("Invalid season or episode number")
        return title, season, episode

    def parse_directory_name(self, dirname: str) -> Tuple[bool, str, int, int]:
        """
        Extract show title from the directory name.

        Parameters
        ----------
        dirname : str
            The directory name to parse

        Returns
        -------
        tuple
            (success, title, season, episode) where:
            - success (bool): Whether a title could be extracted
            - title (str): Show title extracted from directory name
            - season (int): Defaults to 1
            - episode (int): Defaults to 0 (indicating all episodes)
        """
        title = basename(dirname.rstrip("/"))

        if not title or title in [".", "..", "/"]:
            self.logger.debug(f"Directory name '{title}' is not usable")
            return False, "", 1, 0

        common_dirs = [
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
        ]
        if title.lower() in common_dirs:
            self.logger.debug(
                f"Directory name '{title}' is a common system directory, skipping"
            )
            return False, "", 1, 0

        title = title.replace("_", " ").replace(".", " ").strip()

        if len(title) < 3:
            self.logger.debug(
                f"Directory name '{title}' too short, likely not a show title"
            )
            return False, "", 1, 0

        self.logger.debug(f"Parsed title from directory name: {title}")

        return True, title, 1, 0

    def find_anime_title_in_path(self, path: str) -> Tuple[str, int, int]:
        """
        Recursively search for an anime title in the path, trying parent directories
        if necessary.

        Parameters
        ----------
        path : str
            Starting directory path

        Returns
        -------
        tuple
            (title, season, episode) - anime title and defaults for season and episode

        Raises
        ------
        ValueError
            If no suitable directory name is found up to root
        """
        original_path = path
        path = abspath(path)

        while path and path != "/":
            success, title, season, episode = self.parse_directory_name(path)

            if success:
                self.logger.debug(f"Found anime title '{title}' from directory: {path}")
                return title, season, episode

            self.logger.debug(f"No anime title in '{path}', trying parent directory")
            parent_path = dirname(path)

            if parent_path == path:
                break

            path = parent_path

        self.logger.error(
            f"Could not extract anime title from directory path: {original_path}"
        )
        self.logger.error("Please specify a directory with a recognizable anime name")
        raise ValueError(f"Could not find anime title in path: {original_path}")

    def load_cached_anilist_id(self, directory: str) -> Optional[int]:
        """
        Look for a file named '.anilist.id' in the given directory and return the AniList ID.

        Parameters
        ----------
        directory : str
            Path to the directory to search for cache file

        Returns
        -------
        int or None
            The cached AniList ID if found and valid, None otherwise
        """
        cache_path = join(directory, ".anilist.id")
        if exists(cache_path):
            try:
                with open(cache_path, "r", encoding="UTF-8") as f:
                    return int(f.read().strip())
            except Exception:
                self.logger.warning("Failed to read cached AniList ID.")
                return None
        return None

    def save_anilist_id(self, directory: str, anilist_id: int) -> None:
        """
        Save the AniList ID to a file named '.anilist.id' in the given directory.

        Parameters
        ----------
        directory : str
            Path to the directory where the cache file should be saved
        anilist_id : int
            The AniList ID to cache

        Returns
        -------
        None
        """
        cache_path = join(directory, ".anilist.id")
        try:
            with open(cache_path, "w") as f:
                f.write(str(anilist_id))
        except Exception as e:
            self.logger.warning(f"Could not save AniList cache file: {e}")

    def query_anilist(self, title: str, season: Optional[int] = None) -> int:
        """
        Query AniList's GraphQL API for the given title and return its media ID.

        Parameters
        ----------
        title : str
            The anime title to search for
        season : int, optional
            The season number to search for

        Returns
        -------
        int
            The AniList media ID for the title

        Raises
        ------
        ValueError
            If no media is found or an error occurs with the API
        """
        query = """
        query ($search: String) {
          Media(search: $search, type: ANIME) {
            id
            title {
              romaji
              english
              native
            }
            synonyms
          }
        }
        """

        # Clean up the title to remove special characters and extra spaces
        cleaned_title = sub(r"[^\w\s]", "", title).strip()

        # Append season to the title if season is greater than 1
        if season and season > 1:
            cleaned_title += f" - Season {season}"

        variables = {
            "search": cleaned_title
        }

        try:
            self.logger.debug("Querying AniList API for title: %s", title)
            self.logger.debug(f"Query variables: {variables}")
            response = requests_post(
                self.ANILIST_API_URL, json={"query": query, "variables": variables}
            )
            response.raise_for_status()
            data = response.json()

            media = data.get("data", {}).get("Media")
            if media:
                anilist_id = media.get("id")
                self.logger.info(f"Found AniList ID: {anilist_id}")
                return anilist_id

            # If all automatic methods fail, raise ValueError
            self.logger.error(
                f"AniList search failed for title: {title}, season: {season}"
            )
            raise ValueError(f"Could not find anime on AniList for title: {title}")

        except Exception as e:
            self.logger.error(f"Error querying AniList: {e}")
            raise ValueError(f"Error querying AniList API: {str(e)}")

    def _prompt_for_anilist_id(self, title: str) -> int:
        """
        Prompt the user to manually enter an AniList ID.
        """
        print(f"\nPlease find the AniList ID for: {title}")
        print("Visit https://anilist.co and search for your anime.")
        print(
            "The ID is the number in the URL, e.g., https://anilist.co/anime/12345 -> ID is 12345"
        )

        while True:
            try:
                anilist_id = int(input("Enter AniList ID: ").strip())
                return anilist_id
            except ValueError:
                print("Please enter a valid number.")

    def query_jimaku_entries(self, anilist_id: int) -> List[Dict[str, Any]]:
        """
        Query the Jimaku API to list available subtitle entries.

        Parameters
        ----------
        anilist_id : int
            The AniList ID of the anime

        Returns
        -------
        list
            List of entry dictionaries containing subtitle metadata

        Raises
        ------
        ValueError
            If no entries are found or an error occurs with the API
        """
        if not self.api_token:
            raise ValueError(
                "API token is required for downloading subtitles from Jimaku. "
                "Set it in the constructor or JIMAKU_API_TOKEN env var."
            )

        params = {"anilist_id": anilist_id}
        headers = {
            "Authorization": f"{self.api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            self.logger.debug(f"Querying Jimaku entries for AniList ID: {anilist_id}")
            response = requests_get(
                self.JIMAKU_SEARCH_URL, params=params, headers=headers
            )
            response.raise_for_status()
            results = response.json()
            self.logger.debug(f"Jimaku search response: {results}")
            if not results:
                self.logger.error("No subtitle entries found on Jimaku for this media.")
                raise ValueError(
                    f"No subtitle entries found for AniList ID: {anilist_id}"
                )
            return results
        except Exception as e:
            self.logger.error(f"Error querying Jimaku API: {e}")
            raise ValueError(f"Error querying Jimaku API: {str(e)}")

    def get_entry_files(self, entry_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Retrieve file information for a given entry ID.

        Parameters
        ----------
        entry_id : str or int
            The Jimaku entry ID to retrieve files for

        Returns
        -------
        list
            List of file info dictionaries

        Raises
        ------
        ValueError
            If no files are found or an error occurs with the API
        """
        if not self.api_token:
            raise ValueError(
                "API token is required for downloading subtitles from Jimaku. "
                "Set it in the constructor or JIMAKU_API_TOKEN env var."
            )

        url = f"{self.JIMAKU_FILES_BASE}/{entry_id}/files"
        headers = {
            "Authorization": f"{self.api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            self.logger.debug(f"Querying files for entry ID: {entry_id}")
            response = requests_get(url, headers=headers)
            response.raise_for_status()
            files = response.json()
            self.logger.debug(f"Entry files response: {files}")
            if not files:
                self.logger.error("No files found for the selected entry.")
                raise ValueError(f"No files found for entry ID: {entry_id}")
            return files
        except Exception as e:
            self.logger.error(f"Error querying files for entry {entry_id}: {e}")
            raise ValueError(f"Error retrieving files: {str(e)}")

    def filter_files_by_episode(
        self, files: List[Dict[str, Any]], target_episode: int
    ) -> List[Dict[str, Any]]:
        """
        Filter subtitle files to only include those matching the target episode.

        Parameters
        ----------
        files : list
            List of file info dictionaries
        target_episode : int
            Episode number to filter by

        Returns
        -------
        list
            Filtered list of file info dictionaries matching the target episode,
            or all files if no matches are found
        """
        specific_matches = []
        episode_patterns = [
            re_compile(r"[Ee](?:p(?:isode)?)?[ ._-]*(\d+)", IGNORECASE),
            re_compile(r"(?:^|\s|[._-])(\d+)(?:\s|$|[._-])", IGNORECASE),
            re_compile(r"#(\d+)", IGNORECASE),
        ]

        all_episodes_keywords = ["all", "batch", "complete", "season", "full"]
        batch_files = []
        has_specific_match = False

        # First pass: find exact episode matches
        for file_info in files:
            filename = file_info.get("name", "").lower()
            matched = False

            # Try to match specific episode numbers
            for pattern in episode_patterns:
                matches = pattern.findall(filename)
                for match in matches:
                    try:
                        file_episode = int(match)
                        if file_episode == target_episode:
                            specific_matches.append(file_info)
                            self.logger.debug(
                                f"Matched episode {target_episode} in: {filename}"
                            )
                            matched = True
                            has_specific_match = True
                            break
                    except (ValueError, TypeError):
                        continue
                if matched:
                    break

            # Identify batch files
            if not matched:
                might_include_episode = any(
                    keyword in filename for keyword in all_episodes_keywords
                )
                if might_include_episode:
                    self.logger.debug(f"Potential batch file: {filename}")
                    batch_files.append(file_info)

        # Always include batch files, but sort them to the end
        filtered_files = specific_matches + batch_files

        if filtered_files:
            total_specific = len(specific_matches)
            total_batch = len(batch_files)
            self.logger.info(
                f"Found {len(filtered_files)} files matching episode {target_episode} "
                f"({total_specific} specific matches, {total_batch} batch files)"
            )
            return filtered_files
        else:
            self.logger.warning(
                f"No files matched episode {target_episode}, showing all options"
            )
            return files

    def fzf_menu(
        self, options: List[str], multi: bool = False
    ) -> Union[str, List[str], None]:
        """
        Launch fzf with the provided options for selection.

        Parameters
        ----------
        options : list
            List of strings to present as options
        multi : bool, optional
            Whether to enable multi-select mode (default: False)

        Returns
        -------
        str or list or None
            If multi=False: Selected option string or None if cancelled
            If multi=True: List of selected option strings or empty list if cancelled
        """
        try:
            fzf_args = ["fzf", "--height=40%", "--border"]
            if multi:
                fzf_args.append("--multi")
                self.logger.debug("Launching fzf multi-selection menu")
            else:
                self.logger.debug("Launching fzf single selection menu")

            proc = subprocess_run(
                fzf_args,
                input="\n".join(options),
                text=True,
                capture_output=True,
                check=True,
            )

            if multi:
                return [
                    line.strip()
                    for line in proc.stdout.strip().split("\n")
                    if line.strip()
                ]
            else:
                return proc.stdout.strip()

        except CalledProcessError:
            self.logger.warning("User cancelled fzf selection")
            return [] if multi else None

    def download_file(self, url: str, dest_path: str) -> str:
        """
        Download the file from the given URL and save it to dest_path.

        Parameters
        ----------
        url : str
            URL to download the file from
        dest_path : str
            Path where the file should be saved

        Returns
        -------
        str
            Path where the file was saved

        Raises
        ------
        ValueError
            If an error occurs during download
        """
        try:
            self.logger.debug(f"Downloading file from: {url}")
            response = requests_get(url, stream=True)
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.logger.debug(f"File saved to: {dest_path}")
            return dest_path
        except Exception as e:
            self.logger.error(f"Error downloading subtitle file: {e}")
            raise ValueError(f"Error downloading file: {str(e)}")

    def download_subtitles(
        self,
        media_path: str,
        dest_dir: Optional[str] = None,
        play: bool = False,
        anilist_id: Optional[int] = None,
    ) -> List[str]:
        """
        Download subtitles for the given media path.

        This is the main entry point method that orchestrates the entire download process.

        Parameters
        ----------
        media_path : str
            Path to the media file or directory
        dest_dir : str, optional
            Directory to save downloaded subtitles (default: same directory as media)
        play : bool, default=False
            Whether to launch MPV with the subtitles after download
        anilist_id : int, optional
            AniList ID to use directly instead of searching

        Returns
        -------
        list
            List of paths to downloaded subtitle files

        Raises
        ------
        ValueError
            If media path doesn't exist or other errors occur
        """
        if not exists(media_path):
            raise ValueError(f"Path '{media_path}' does not exist")

        self.logger.info("Starting subtitle search and download process")

        is_directory = self.is_directory_input(media_path)
        self.logger.info(
            f"Processing {'directory' if is_directory else 'file'}: {media_path}"
        )

        if dest_dir:
            dest_dir = dest_dir
        else:
            if is_directory:
                dest_dir = media_path
            else:
                dest_dir = dirname(abspath(media_path))

        self.logger.debug(f"Destination directory: {dest_dir}")

        if is_directory:
            title, season, episode = self.find_anime_title_in_path(media_path)
            media_dir = media_path
            media_file = None
            self.logger.debug(
                f"Found anime title '{title}' but will save subtitles to: {dest_dir}"
            )
        else:
            base_filename = basename(media_path)
            title, season, episode = self.parse_filename(base_filename)
            media_dir = dirname(abspath(media_path))
            media_file = media_path

        self.logger.info(
            f"Identified show: {title}, Season: {season}, Episode: {episode}"
        )

        if anilist_id is None:
            anilist_id = self.load_cached_anilist_id(media_dir)

        if not anilist_id:
            self.logger.info("Querying AniList for media ID...")
            anilist_id = self.query_anilist(title, season)
            self.logger.info(f"AniList ID for '{title}' is {anilist_id}")
            self.save_anilist_id(media_dir, anilist_id)
        else:
            self.logger.info(
                f"Using {'provided' if anilist_id else 'cached'} AniList ID: {anilist_id}"
            )

        # Now check for API token before making Jimaku API calls
        if not self.api_token:
            self.logger.error(
                "Jimaku API token is required to download subtitles. "
                "Please set it with --token or the JIMAKU_API_TOKEN environment variable."
            )
            raise ValueError(
                "Jimaku API token is required to download subtitles. "
                "Please set it with --token or the JIMAKU_API_TOKEN environment variable."
            )

        self.logger.info("Querying Jimaku for subtitle entries...")
        entries = self.query_jimaku_entries(anilist_id)

        if not entries:
            raise ValueError("No subtitle entries found for AniList ID")

        entry_options = []
        entry_mapping = {}
        for i, entry in enumerate(entries, start=1):
            opt = f"{i}. {entry.get('english_name', 'No Eng Name')} - {entry.get('japanese_name', 'None')}"
            entry_options.append(opt)
            entry_mapping[opt] = entry

        entry_options.sort()

        self.logger.info("Select a subtitle entry using fzf:")
        selected_entry_option = self.fzf_menu(entry_options, multi=False)
        if not selected_entry_option or selected_entry_option not in entry_mapping:
            raise ValueError("No valid entry selected")

        selected_entry = entry_mapping[selected_entry_option]
        entry_id = selected_entry.get("id")
        if not entry_id:
            raise ValueError("Selected entry does not have a valid ID")

        self.logger.info(f"Retrieving files for entry ID: {entry_id}")
        files = self.get_entry_files(entry_id)

        if not is_directory and episode > 0:
            self.logger.info(f"Filtering subtitle files for episode {episode}")
            files = self.filter_files_by_episode(files, episode)

        file_options = []
        file_mapping = {}
        for i, file_info in enumerate(files, start=1):
            display = f"{i}. {file_info.get('name', 'Unknown')}"
            file_options.append(display)
            file_mapping[display] = file_info

        file_options.sort()

        self.logger.info(
            f"Select {'one or more' if is_directory else 'one'} subtitle file(s):"
        )
        selected_files = self.fzf_menu(file_options, multi=is_directory)

        if is_directory:
            if not selected_files:
                raise ValueError("No subtitle files selected")
            selected_files_list = selected_files
        else:
            if not selected_files:
                raise ValueError("No subtitle file selected")
            selected_files_list = [selected_files]

        downloaded_files = []
        for opt in selected_files_list:
            file_info = file_mapping.get(opt)
            if not file_info:
                self.logger.warning(f"Could not find mapping for selected file: {opt}")
                continue

            download_url = file_info.get("url")
            if not download_url:
                self.logger.warning(
                    f"File option '{opt}' does not have a download URL. Skipping."
                )
                continue

            filename = file_info.get("name")
            if not filename:
                if is_directory:
                    filename = f"{file_info.get('name', 'subtitle.srt')}"

            dest_path = join(dest_dir, filename)
            self.logger.info(f"Downloading '{opt}' to {dest_path}...")
            self.download_file(download_url, dest_path)
            downloaded_files.append(dest_path)
            self.logger.info(f"Subtitle saved to: {dest_path}")

        if play and not is_directory:
            self.logger.info("Launching MPV with the subtitle files...")
            mpv_cmd = ["mpv", media_file]
            mpv_cmd.extend([f"--sub-file={filename}"])
            try:
                self.logger.debug(f"Running command: {' '.join(mpv_cmd)}")
                subprocess_run(mpv_cmd)
            except FileNotFoundError:
                self.logger.error(
                    "MPV not found. Please install MPV and ensure it is in your PATH."
                )
        elif play and is_directory:
            self.logger.warning(
                "Cannot play media with MPV when input is a directory. Skipping playback."
            )

        self.logger.info("Subtitle download process completed successfully")
        return downloaded_files
