# Jimaku-DL

<a href="">[![AUR License](https://img.shields.io/aur/license/python-jimaku-dl)](https://aur.archlinux.org/packages/python-jimaku-dl)</a>
<a href="">[![GitHub Release](https://img.shields.io/github/v/release/ksyasuda/jimaku-dl)](https://github.com/ksyasuda/jimaku-dl)</a>
<a href="">[![AUR Last Modified](https://img.shields.io/aur/last-modified/python-jimaku-dl)](https://aur.archlinux.org/packages/python-jimaku-dl)</a>
<a href="">[![codecov](https://codecov.io/gh/ksyasuda/jimaku-dl/graph/badge.svg?token=5S5NRSPVHT)](https://codecov.io/gh/ksyasuda/jimaku-dl)</a>

<div align="center">
  
A tool for downloading Japanese subtitles for anime from <a href="https://jimaku.cc" target="_blank" rel="noopener noreferrer">Jimaku</a>

<p>
  <video autoplay loop muted playsinline src="https://github.com/user-attachments/assets/6cf63a3e-f9a6-41e3-9351-d37a76d882e9" type="video/mp4">
  <img src="https://github.com/user-attachments/assets/f65d4e47-59f9-4cd1-be72-46a512af7fe1" alt="Jimaku-DL Demo">
</p>
   
</div>

## Features

- Download subtitles from Jimaku.cc
- Automatic subtitle synchronization with video (requires ffsubsync)
- Playback with MPV player and Japanese audio track selection
- On-screen notification when subtitle synchronization is complete
- Background synchronization during playback
- Cross-platform support (Windows, macOS, Linux)
- Smart filename and directory parsing for anime detection
- Cache AniList IDs for faster repeat usage
- Interactive subtitle selection with fzf

## Installation

```bash
pip install jimaku-dl
```

### Requirements

- Python 3.8+
- fzf for interactive selection menus (required)
- MPV for video playback (optional)
- ffsubsync for subtitle synchronization (optional)

## Usage

```bash
# Basic usage - Download subtitles for a video file
jimaku-dl /path/to/your/anime.mkv

# Download subtitles and play video immediately
jimaku-dl /path/to/your/anime.mkv --play

# Download, play, and synchronize subtitles in background
jimaku-dl /path/to/your/anime.mkv --play --sync

# Download subtitles for all episodes in a directory
jimaku-dl /path/to/your/anime/season-1/

# Specify custom destination directory
jimaku-dl /path/to/your/anime.mkv --dest-dir /path/to/subtitles
```

### API Token

You'll need a Jimaku API token to use this tool. Set it using one of these methods:

1. Command line option:

   ```bash
   jimaku-dl /path/to/anime.mkv --token YOUR_TOKEN_HERE
   ```

2. Environment variable:
   ```bash
   export JIMAKU_API_TOKEN="your-token-here"
   jimaku-dl /path/to/anime.mkv
   ```

## Command-Line Options

```bash
usage: jimaku-dl [options] MEDIA_PATH

positional arguments:
  MEDIA_PATH            Path to media file or directory

options:
  -h, --help            Show this help message and exit
  -v, --version         Show program version number and exit
  -t TOKEN, --token TOKEN
                        Jimaku API token (can also use JIMAKU_API_TOKEN env var)
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set logging level
  -d DEST_DIR, --dest-dir DEST_DIR
                        Destination directory for subtitles
  -p, --play           Play media with MPV after download
  -a ANILIST_ID, --anilist-id ANILIST_ID
                        AniList ID (skip search)
  -s, --sync           Sync subtitles with video in background when playing
```

## File Naming

Jimaku Downloader supports various file naming conventions to extract show title, season, and episode information. It is recommended to follow the [Trash Guides recommended naming schema](https://trash-guides.info/Sonarr/Sonarr-recommended-naming-scheme/#recommended-naming-scheme) for best results.

### Examples

- `Show Title - S01E02 - Episode Name [1080p].mkv`
- `Show.Name.S01E02.1080p.mkv`
- `Show_Name_S01E02_HEVC.mkv`
- `/path/to/Show Name/Season-1/Show Name - 02 [1080p].mkv`

## Development

To contribute to Jimaku Downloader, follow these steps:

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/jimaku-dl.git
   cd jimaku-dl
   ```

2. Create a virtual environment and activate it:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the dependencies:

   ```sh
   pip install -r requirements.txt
   pip install -r requirements_dev.txt
   ```

4. Run the tests:

   ```sh
   pytest
   ```

## License

Jimaku Downloader is licensed under the GPLv3 License. See the [LICENSE](LICENSE) file for more information.
