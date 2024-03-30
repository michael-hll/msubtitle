import os
from enum import StrEnum


class C(StrEnum):
  UUID = 'uuid'
  TEMP = 'temp'
  AAC = 'aac'
  SRT = 'srt'
  SRT_T = 'srt_t'
  SIZE = 'size'
  START = 'start'
  END = 'end'
  DURATION = 'duration'
  OUT = 'out'
  TEMP_DIR = os.path.join(os.getcwd(), "temp")


class ARGS(StrEnum):
  VIDEO = 'video'
  INPUT_DIR = 'input_dir'
  MODEL = 'model'
  OUTPUT_DIR = 'output_dir'
  SRT_ONLY = 'srt_only'
  VERBOSE = 'verbose'
  TASK = 'task'
  LANGUAGE = 'language'
  GEMINI_MODEL = 'gemini_model'
  LANGUAGE_TO = 'language_to'
