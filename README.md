# Jimaku Subtitle Downloader

A Python package to automate download japanese subtitles for anime from [jimaku.cc](https://jimaku.cc/)

## Features

- Search for subtitles using AniList IDs
- Supports both individual files and directories
- Interactive subtitle selection using fzf
- Auto-detects anime from filenames with season and episode numbers
- Optional MPV playback with downloaded subtitles
- Caches AniList IDs to reduce API calls

## Installation

### PIP

```bash
pip install jimaku-dl
```

### Arch Linux

```bash
paru -S python-jimaku-dl
# or
yay -S python-jimaku-dl
```

### From source

```bash
git clone https://github.com/ksyasuda/jimaku-dl.git
cd jimaku-dl
pip install -e .
```

## Usage

### Command Line

````bash

```bash
# Download subtitles for a video file
jimaku-dl /path/to/your/anime.S01E02.mkv

# Download subtitles for an entire series (directory mode)
jimaku-dl /path/to/your/anime/directory/

# Specify a different destination directory
jimaku-dl /path/to/your/anime.mkv --dest /path/to/subtitles/

# Play the video with MPV after downloading subtitles
jimaku-dl /path/to/your/anime.mkv --play

# Set API token via command line
jimaku-dl /path/to/your/anime.mkv --api-token YOUR_TOKEN
````

### Python Class

```python
from jimaku_downloader import JimakuDownloader

# Create a downloader instance
downloader = JimakuDownloader(api_token="your_api_token", log_level="INFO")

# Download subtitles
downloaded_files = downloader.download_subtitles(
    media_path="/path/to/your/anime.mkv",
    dest_dir="/path/to/save/subtitles/",  # Optional
    play=True  # Optional: play with MPV after downloading
)

print(f"Downloaded {len/downloaded_files)} subtitle files")
```

#### Environment Variables

You can set your Jimaku API token using the `JIMAKU_API_TOKEN` environment variable:

```bash
export JIMAKU_API_TOKEN=your_api_token
```

## Requirements

- Python 3.8 or higher
- `fzf` command-line utility for interactive selection
- `mpv` (optional, for playback functionality)
- A valid [jimaku.cc](https://jimaku.cc/) API token

## License

GPL v3
