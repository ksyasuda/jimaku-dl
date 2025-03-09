# Jimaku Downloader

<div align="center">
  <a href="">[![AUR License](https://img.shields.io/aur/license/python-jimaku-dl)](https://aur.archlinux.org/packages/python-jimaku-dl)</a>
  <a href="">[![GitHub Release](https://img.shields.io/github/v/release/ksyasuda/jimaku-dl)](https://github.com/ksyasuda/jimaku-dl)</a>
  <a href="">[![AUR Last Modified](https://img.shields.io/aur/last-modified/python-jimaku-dl)](https://aur.archlinux.org/packages/python-jimaku-dl)</a>
  <a href="">[![codecov](https://codecov.io/gh/ksyasuda/jimaku-dl/graph/badge.svg?token=5S5NRSPVHT)](https://codecov.io/gh/ksyasuda/jimaku-dl)</a>

A tool for downloading Japanese subtitles for anime from <a href="https://jimaku.cc" target="_blank" rel="noopener noreferrer">Jimaku</a>

  <p>
    <video controls muted src="https://github.com/user-attachments/assets/3723866f-4e7d-4f89-8b55-17f2fb6fa6be"></video>
  </p>
</div>

## Features

- Queries AniList for anime titles
- Select subtitle entries from Jimaku
- Download subtitles to a specified directory
- Launch MPV with the downloaded subtitles
- Supports both file and directory inputs
  - Support for downloading multiple subtitle files

## Installation

You can install Jimaku Downloader using pip

```sh
pip install jimaku-dl
```

### Arch Linux

Arch Linux users can install
<a href="https://aur.archlinux.org/packages/python-jimaku-dl" target="_blank">python-jimaku-dl</a>
from the AUR

```sh
paru -S python-jimaku-dl
# or
yay -S python-jimaku-dl

```

## Usage

### Command Line Interface

The main entry point for Jimaku Downloader is the `jimaku-dl` command. Here are some examples of how to use it:

```sh
# Download subtitles for a single video file
jimaku-dl /path/to/video.mkv

# Download subtitles for a directory
jimaku-dl /path/to/anime/directory

# Specify a custom destination directory
jimaku-dl /path/to/video.mkv --dest /custom/path

# Launch MPV with the downloaded subtitles
jimaku-dl /path/to/video.mkv --play

# Specify an AniList ID directly
jimaku-dl /path/to/video.mkv --anilist-id 123456

# Set the Jimaku API token
jimaku-dl /path/to/video.mkv --token your_api_token

# Set the logging level
jimaku-dl /path/to/video.mkv --log-level DEBUG
```

### Python API

You can also use Jimaku Downloader as a Python library:

```python
from jimaku_dl.downloader import JimakuDownloader

downloader = JimakuDownloader(api_token="your_api_token", log_level="INFO")
downloaded_files = downloader.download_subtitles("/path/to/video.mkv", dest_dir="/custom/path", play=True)
print(f"Downloaded files: {downloaded_files}")
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
