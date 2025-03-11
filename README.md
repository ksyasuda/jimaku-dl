# Jimaku-DL

A tool for downloading and synchronizing anime subtitles from Jimaku.cc.

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

- Search for anime titles using the AniList API
- Download subtitles from Jimaku.cc
- Automatically synchronize subtitles with video files using ffsubsync
- Play media with downloaded subtitles using MPV
- Check and reuse existing synchronized subtitle files
- Automatic playback with MPV after download
- Background synchronization of subtitles with video (requires ffsubsync)

## Installation

```bash
pip install jimaku-dl
```

### Requirements

- Python 3.7+
- MPV for playing videos (optional)
- ffsubsync for subtitle synchronization (optional)
- fzf for interactive selection menus (required)

## Usage

Jimaku-DL provides a simple command line interface for downloading and synchronizing subtitles.

```bash
# Basic usage - download subtitles for a video file
jimaku-dl download /path/to/your/anime.mkv

# Download subtitles, sync in background, and play the video with MPV
jimaku-dl download /path/to/your/anime.mkv --play --sync

# Download subtitles for all episodes in a directory
jimaku-dl download /path/to/your/anime/season-1/
```

> **Note**: For backward compatibility, the `download` subcommand can be omitted:  
> `jimaku-dl /path/to/your/anime.mkv --play`

### Synchronizing Existing Subtitles

```bash
# Synchronize existing subtitle file with a video
jimaku-dl sync /path/to/video.mkv /path/to/subtitles.srt

# Specify output path for synchronized subtitles
jimaku-dl sync /path/to/video.mkv /path/to/subtitles.srt --output /path/to/output.srt
```

### API Token

You'll need a Jimaku API token to use this tool. You can set it in two ways:

1. Using the `--token` flag:
   ```bash
   jimaku-dl download /path/to/anime.mkv --token YOUR_TOKEN_HERE
   ```

2. Setting the `JIMAKU_API_TOKEN` environment variable:
   ```bash
   export JIMAKU_API_TOKEN="your-token-here"
   jimaku-dl download /path/to/anime.mkv
   ```

## How It Works

1. **Search**: Jimaku-DL analyzes your media file name or directory structure to identify the anime title, season, and episode.
2. **AniList ID**: It queries the AniList API to get the media ID, which is cached for future use.
3. **Subtitle Selection**: You'll be presented with a menu to choose subtitle entries and files matching your media.
4. **Download**: The selected subtitle file is downloaded to your media directory.
5. **Synchronization**: If requested, the subtitle is synchronized with the video using ffsubsync.
6. **Playback**: If requested, the media is played with MPV using the downloaded (and optionally synchronized) subtitles.

## Advanced Features

### Reusing Existing Synchronized Subtitles

If you run the tool on a file that already has synchronized subtitles, you'll be prompted to:
- Use the existing synced file
- Create a new synced file
- Cancel synchronization

This saves time when you've already synchronized subtitles for a file.

### Background Synchronization During Playback

When using the `--play` option, your video starts playing immediately. If you also use `--sync`, the subtitle synchronization happens in the background, and the subtitles are automatically updated once synchronization is complete.

## Options

### Global Options
- `-t, --token TOKEN`: Jimaku API token
- `-l, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`: Set logging level

### Download Options
- `-d, --dest-dir DIR`: Destination directory for subtitles
- `-p, --play`: Play media with MPV after download
- `-s, --sync`: Synchronize subtitles with video
- `-a, --anilist-id ID`: Specify AniList ID to skip search

### Sync Options
- `-o, --output PATH`: Output path for synchronized subtitles

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

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
