import os
import sys
from typing import Iterator, TextIO
import subprocess


def str2bool(string):
  string = string.lower()
  str2val = {"true": True, "false": False}

  if string in str2val:
    return str2val[string]
  else:
    raise ValueError(
        f"Expected one of {set(str2val.keys())}, got {string}")


def format_timestamp(seconds: float, always_include_hours: bool = False):
  assert seconds >= 0, "non-negative timestamp expected"
  milliseconds = round(seconds * 1000.0)

  hours = milliseconds // 3_600_000
  milliseconds -= hours * 3_600_000

  minutes = milliseconds // 60_000
  milliseconds -= minutes * 60_000

  seconds = milliseconds // 1_000
  milliseconds -= seconds * 1_000

  hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
  return f"{hours_marker}{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def write_srt(transcript: Iterator[dict], file: TextIO):
  for i, segment in enumerate(transcript, start=1):
    print(
        f"{i}\n"
        f"{format_timestamp(segment['start'], always_include_hours=True)} --> "
        f"{format_timestamp(segment['end'], always_include_hours=True)}\n"
        f"{segment['text'].strip().replace('-->', '->')}\n",
        file=file,
        flush=True,
    )


def filename(path):
  return os.path.splitext(os.path.basename(path))[0]


def run_ffmpeg_command(cmd, verbose=False):
  print('==> running FFmpeg command: ' + cmd)
  # use shell to run ffmpeg
  stdout_val = subprocess.PIPE
  stderr_val = subprocess.PIPE
  if verbose:
    stdout_val = sys.stdout
    stderr_val = sys.stdout

  process = subprocess.Popen(
      cmd, shell=True,
      stdout=stdout_val,
      stderr=stderr_val)

  # waiting the result and return
  process.communicate()
  if process.returncode != 0:
    if verbose:
      print('==> FFmpeg command runn failed!')
    return False
  else:
    if verbose:
      print('==> FFmpeg command run success!')
    return True


def sizeof_fmt(num: int, suffix="B"):
  for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
    if abs(num) < 1024.0:
      return f"[size: {num:3.1f}{unit}{suffix}]"
    num /= 1024.0
  return f"[size of: {num:.1f}Y{suffix}]"


def format_seconds(seconds: int):
  minutes, seconds = divmod(seconds, 60)
  hours, minutes = divmod(minutes, 60)
  days, hours = divmod(hours, 24)

  time_string = ""
  if days > 0:
    time_string += "{:d} days, ".format(int(days))
  if hours > 0:
    time_string += "{:d} hours, ".format(int(hours))
  if minutes > 0:
    time_string += "{:d} minutes, ".format(int(minutes))
  time_string += "{:.2f} seconds".format(seconds)

  return time_string
