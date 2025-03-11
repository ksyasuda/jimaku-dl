#!/usr/bin/env python3
import argparse
import sys
import os
from os import environ, path
from typing import Optional, Sequence
from subprocess import DEVNULL, run as subprocess_run, Popen
import time
import tempfile
import threading
import socket
import json
import logging

from jimaku_dl import __version__  # Import version from package
from jimaku_dl.downloader import JimakuDownloader, FFSUBSYNC_AVAILABLE

def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """
    Parse command line arguments for jimaku-dl.

    Parameters
    ----------
    args : sequence of str, optional
        Command line argument strings. If None, sys.argv[1:] is used.

    Returns
    -------
    argparse.Namespace
        Object containing argument values as attributes
    """
    parser = argparse.ArgumentParser(
        description="Download and manage anime subtitles from Jimaku"
    )

    # Add version argument
    parser.add_argument(
        "-v", "--version", 
        action="version", 
        version=f"jimaku-dl {__version__}"
    )

    # Global options
    parser.add_argument(
        "-t", "--token",
        help="Jimaku API token (can also use JIMAKU_API_TOKEN env var)",
    )
    parser.add_argument(
        "-l", "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level",
    )
    
    # Main functionality options
    parser.add_argument(
        "media_path", 
        help="Path to media file or directory"
    )
    parser.add_argument(
        "-d", "--dest-dir", 
        help="Destination directory for subtitles"
    )
    parser.add_argument(
        "-p", "--play", 
        action="store_true", 
        help="Play media with MPV after download"
    )
    parser.add_argument(
        "-a", "--anilist-id", 
        type=int, 
        help="AniList ID (skip search)"
    )
    parser.add_argument(
        "-s", "--sync", 
        action="store_true", 
        help="Sync subtitles with video in background when playing"
    )
    
    return parser.parse_args(args)

def sync_subtitles_thread(video_path: str, subtitle_path: str, output_path: str, socket_path: str):
    """
    Run subtitle synchronization in a separate thread and update MPV when done.
    
    This function runs in a background thread to synchronize subtitles and then
    update the MPV player through its socket interface.
    """
    logger = logging.getLogger("jimaku_sync")
    handler = logging.FileHandler(path.expanduser("~/.jimaku-sync.log"))
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    try:
        logger.info(f"Starting sync: {video_path} -> {output_path}")
        
        # Run ffsubsync directly through subprocess
        result = subprocess_run(
            ["ffsubsync", video_path, "-i", subtitle_path, "-o", output_path],
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0 or not path.exists(output_path):
            logger.error(f"Synchronization failed: {result.stderr}")
            print(f"Sync failed: {result.stderr}")
            return
        
        print("Synchronization successful!")
        logger.info(f"Sync successful: {output_path}")
        
        # Wait for the socket to be ready (MPV might still be initializing)
        start_time = time.time()
        max_wait = 10  # Maximum wait time in seconds
        
        while not path.exists(socket_path) and time.time() - start_time < max_wait:
            time.sleep(0.5)
            
        if not path.exists(socket_path):
            logger.error(f"Socket not found after waiting: {socket_path}")
            return
            
        # Connect to the MPV socket and send commands with proper error handling
        try:
            time.sleep(0.5)  # Give MPV a moment to initialize the socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(0.5)  # Short timeout for reads
            sock.connect(socket_path)
            
            # Helper function to send command and read response
            def send_command(cmd):
                try:
                    sock.send(json.dumps(cmd).encode("utf-8") + b"\n")
                    # Try to read response to keep connection synchronized
                    try:
                        response = sock.recv(1024)
                        logger.debug(f"MPV response: {response.decode('utf-8', errors='ignore')}")
                    except socket.timeout:
                        pass  # Expected when MPV doesn't respond immediately
                    time.sleep(0.1)  # Brief pause between commands
                except Exception as e:
                    logger.debug(f"Socket send error: {e}")
                    return False
                return True
            
            # Helper function to get highest subtitle track ID
            def get_current_subtitle_count():
                try:
                    sock.send(json.dumps({"command": ["get_property", "track-list"], "request_id": 100}).encode("utf-8") + b"\n")
                    response = sock.recv(4096).decode('utf-8')
                    track_list = json.loads(response)["data"]
                    sub_tracks = [t for t in track_list if t.get("type") == "sub"]
                    return len(sub_tracks)
                except Exception as e:
                    logger.debug(f"Error getting track count: {e}")
                    return 0

            # Commands to update subtitles
            commands = [
                {"command": ["sub-reload"], "request_id": 1},
                {"command": ["sub-add", output_path], "request_id": 2},
            ]
            
            # Send initial commands
            all_succeeded = True
            for cmd in commands:
                if not send_command(cmd):
                    all_succeeded = False
                    break

            # Get the new subtitle ID (should be highest ID)
            if all_succeeded:
                new_sid = get_current_subtitle_count()
                if new_sid > 0:
                    # Select the new subtitle and ensure it's visible
                    final_commands = [
                        {"command": ["set_property", "sub-visibility", "yes"], "request_id": 3},
                        {"command": ["set_property", "sid", new_sid], "request_id": 4},
                    ]
                    for cmd in final_commands:
                        if not send_command(cmd):
                            all_succeeded = False
                            break

            # Clean shutdown of socket connection
            try:
                # Send a no-op command to flush the connection
                send_command({"command": ["ignore"]})
                # Shutdown the write side first
                sock.shutdown(socket.SHUT_WR)
                # Read any remaining data
                while True:
                    try:
                        if not sock.recv(1024):
                            break
                    except socket.timeout:
                        break
                    except socket.error:
                        break
            except Exception as e:
                logger.debug(f"Socket shutdown error: {e}")
            finally:
                sock.close()
            
            if all_succeeded:
                print("Updated MPV with synchronized subtitle")
                logger.info("MPV update complete")
            
        except socket.error as e:
            logger.error(f"Socket connection error: {e}")
            
    except Exception as e:
        logger.exception("Error in synchronization process")
        print(f"Sync error: {e}")

def run_background_sync(video_path: str, subtitle_path: str, output_path: str, socket_path: str):
    """
    Start a background thread to synchronize subtitles and update MPV.

    Parameters
    ----------
    video_path : str
        Path to the video file
    subtitle_path : str
        Path to the subtitle file to synchronize
    output_path : str
        Path where the synchronized subtitle will be saved
    socket_path : str
        Path to MPV's IPC socket
    """
    logger = logging.getLogger("jimaku_sync")
    try:
        sync_thread = threading.Thread(
            target=sync_subtitles_thread,
            args=(video_path, subtitle_path, output_path, socket_path),
            daemon=True,  # Thread will exit when main thread exits
        )
        sync_thread.start()
    except Exception as e:
        logger.error(f"Failed to start sync thread: {e}")

def main(args: Optional[Sequence[str]] = None) -> int:
    """
    Main entry point for the jimaku-dl command line tool.

    Parameters
    ----------
    args : sequence of str, optional
        Command line argument strings. If None, sys.argv[1:] is used.

    Returns
    -------
    int
        Exit code (0 for success, non-zero for errors)
    """
    try:
        parsed_args = parse_args(args)
    except SystemExit as e:
        return e.code

    # Get API token from args or environment
    api_token = parsed_args.token if hasattr(parsed_args, "token") else None
    if not api_token:
        api_token = environ.get("JIMAKU_API_TOKEN", "")

    downloader = JimakuDownloader(api_token=api_token, log_level=parsed_args.log_level)
    
    try:
        # Check if media path exists
        if not path.exists(parsed_args.media_path):
            print(f"Error: Path '{parsed_args.media_path}' does not exist")
            return 1
        
        # If sync requested but ffsubsync is not available, warn the user
        sync_enabled = parsed_args.sync
        if sync_enabled and not FFSUBSYNC_AVAILABLE:
            print("Warning: ffsubsync is not installed. Synchronization will be skipped.")
            print("Install it with: pip install ffsubsync")
            sync_enabled = False
        
        # Download subtitles and prepare for playback
        is_directory = path.isdir(parsed_args.media_path)
        downloaded_files = downloader.download_subtitles(
            parsed_args.media_path,
            dest_dir=parsed_args.dest_dir,
            play=False,  # We'll handle playback ourselves for background sync
            anilist_id=parsed_args.anilist_id,
            sync=sync_enabled,  # Use our validated sync flag
        )
        
        if not downloaded_files:
            print("No subtitles were downloaded")
            return 1

        # If playing a video with sync enabled, handle background sync
        if parsed_args.play and not is_directory:
            media_file = parsed_args.media_path
            subtitle_file = downloaded_files[0]
            
            # Create unique socket path
            socket_path = path.join(tempfile.gettempdir(), f"mpv-jimaku-{int(time.time())}.sock")
            
            # Prepare output path for synchronized subtitle
            if parsed_args.sync:
                base, ext = path.splitext(subtitle_file)
                output_path = f"{base}.synced{ext}"
                
                # Start background sync in a thread
                if FFSUBSYNC_AVAILABLE:
                    run_background_sync(media_file, subtitle_file, output_path, socket_path)
            
            # Get track IDs for better playback
            sid, aid = downloader.get_track_ids(media_file, subtitle_file)
            
            # Prepare mpv command with options to suppress socket error messages
            mpv_cmd = [
                "mpv",
                media_file,
                f"--sub-file={subtitle_file}",
                f"--input-ipc-server={socket_path}",
                # Add options to completely silence IPC-related messages
                "--msg-level=ipc=no,input=no,cplayer=no",  # Silence socket-related messages
                "--log-file=/dev/null",                    # Redirect logs to /dev/null
                "--no-terminal",                           # Disable terminal output
            ]
            
            if sid is not None:
                mpv_cmd.append(f"--sid={sid}")
            if aid is not None:
                mpv_cmd.append(f"--aid={aid}")
            
            # Start MPV with all error messages suppressed
            try:
                subprocess_run(mpv_cmd, stdout=DEVNULL, stderr=DEVNULL, check=False)
            except FileNotFoundError:
                print("Warning: MPV not found. Could not play video.")
                return 1
        
        elif parsed_args.play and is_directory:
            print("Cannot play media with MPV when input is a directory. Skipping playback.")
            
        return 0
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
