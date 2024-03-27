import os
import sys
import whisper
import argparse
import warnings
import shutil
from utils import C, filename, str2bool, write_srt, run_ffmpeg_command, sizeof_fmt, format_seconds
from csrt import translateSrt
import uuid
import glob
from tqdm import tqdm
import time
from tabulate import tabulate

temp_dir = os.path.join(os.getcwd(), "temp")


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("video", nargs="*", type=str,
                      default=None, help="paths to video files to transcribe")
  parser.add_argument("--input_dir", "-i", type=str, nargs='*',
                      default=None, help="directory of mp4 files")
  parser.add_argument("--model", default="small",
                      choices=whisper.available_models(), help="name of the Whisper model to use")
  parser.add_argument("--output_dir", "-o", type=str,
                      default="", help="directory to save the outputs")
  parser.add_argument("--srt_only", type=str2bool, default=False,
                      help="only generate the .srt file and not create overlayed video")
  parser.add_argument("--verbose", type=str2bool, default=False,
                      help="whether to print out the progress and debug messages")
  parser.add_argument("--task", type=str, default="transcribe",
                      choices=["transcribe", "translate"],
                      help="whether to perform X->X speech recognition ('transcribe') or X->English translation ('translate')")
  parser.add_argument("--language", type=str, default="auto",
                      choices=["auto", "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo",
                               "br", "bs", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu",
                               "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht",
                               "hu", "hy", "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko",
                               "la", "lb", "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr",
                               "ms", "mt", "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt",
                               "ro", "ru", "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su",
                               "sv", "sw", "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur",
                               "uz", "vi", "yi", "yo", "zh"],
                      help="What is the origin language of the video? If unset, it is detected automatically.")
  parser.add_argument("--gemini_model", default="",
                      choices=["gemini-pro", "gemini"], help="name of the gemini model")
  parser.add_argument("--language_to", type=str, default="zh",
                      choices=["af", "am", "ar", "as", "az", "ba", "be",
                               "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy", "da", "de", "el",
                               "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha",
                               "haw", "he", "hi", "hr", "ht", "hu", "hy", "id", "is", "it", "ja",
                               "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", "ln", "lo", "lt",
                               "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne",
                               "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru", "sa",
                               "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw",
                               "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz",
                               "vi", "yi", "yo", "zh"],
                      help="The language code to translate the subtitle to using gemini_model")

  args = parser.parse_args().__dict__
  model_name: str = args.pop("model")
  input_dir: str = args.pop("input_dir", None)
  video: str = args.pop("video", None)
  output_dir: str = args.pop("output_dir")
  srt_only: bool = args.pop("srt_only")
  language: str = args.pop("language")
  language_to: str = args.pop("language_to")

  gemini_model: str = args.pop("gemini_model")
  verbose: bool = args["verbose"]

  # get all .mp4 files need to be processed
  to_processed_files = []
  processed_result = {}
  if video:
    if video[0] and not video[0].endswith('.mp4'):
      raise Exception('Only mp4 files can be processed.')
    to_processed_files.append(video[0])
  elif input_dir:
    try:
      input_d = input_dir[0] + "/*.mp4"
      to_processed_files = glob.glob(input_d)
    except Exception as e:
      print(e)
      sys.exit()
  else:
    print('No input video files need to be processed!')
    sys.exit()

  if len(to_processed_files) == 0:
    raise Exception("There is no input mp4 videos found.")
  print('==> processed files:', to_processed_files)

  # check output dir and temp dir
  if not output_dir:
    output_dir = os.path.join(os.getcwd(), 'out')
  os.makedirs(output_dir, exist_ok=True)
  print(f'==> cleanning up files from temp folder: {temp_dir}')
  shutil.rmtree(temp_dir, ignore_errors=True, onerror=None)
  os.makedirs(temp_dir, exist_ok=True)

  # Loading the whisper model
  if model_name.endswith(".en"):
    warnings.warn(
        f"{model_name} is an English-only model, forcing English detection.")
    args["language"] = "en"
  # if translate task used and language argument is set, then use it
  elif language != "auto":
    args["language"] = language

  model = whisper.load_model(model_name)

  # gothrough each mp4 file
  for video in tqdm(to_processed_files, '==> TOTAL PROGRESS: '):

    # copy it to temp folder
    temp_file_id = str(uuid.uuid1())
    temp_video_name = os.path.join(temp_dir, temp_file_id + '.mp4')
    processed_result[video] = {
        C.UUID: "",  # the uuid used to the following temp file names
        C.TEMP: "",  # temp video name
        C.AAC: "",  # temp aac audio file name
        C.SRT: "",  # temp srt file name
        C.SRT_T: "",  # temp srt translation file name
        C.SIZE: "",  # temp video file size
        C.START: time.time(),  # start time
        C.END: 0,  # end time
        C.DURATION: "",  # running duration
    }
    processed_result[video][C.UUID] = temp_file_id
    processed_result[video][C.TEMP] = temp_video_name
    if verbose:
      print(f'==> coping processed mp4 file [{video}] to [{temp_video_name}]')
    shutil.copy(video, temp_video_name)
    processed_result[video][C.SIZE] = sizeof_fmt(
        os.stat(temp_video_name).st_size)

    # get audio file (aac file)
    get_audio(video, processed_result, verbose)

    # get sub_titles (srt file)
    get_subtitles(
        video,
        processed_result,
        lambda audio_path: model.transcribe(audio_path, **args)
    )

    # translate subtitles
    if gemini_model:
      # using google gemini to translate the output srt file
      print(
          f"==> Translating subtitles for '{filename(video)}.mp4' {processed_result[video][C.SIZE]} This might take a while.")
      srt_t_temp_file_name = processed_result[video][C.UUID] + '_t.srt'
      srt_t_path = os.path.join(temp_dir, srt_t_temp_file_name)
      errors = []
      translateSrt(processed_result[video][C.SRT], language_to, srt_t_path,
                   gemini_model, verbose, errors)
      processed_result[video][C.SRT_T] = srt_t_path
      print('==> error item nubmers:', errors)

    # auto add subtitles to the original video
    # using ffmpeg command to achieve this
    if not srt_only:
      temp_video_out_name = processed_result[video][C.UUID] + '.out.mp4'
      temp_video_out_path = os.path.join(temp_dir, temp_video_out_name)
      processed_result[video][C.OUT] = temp_video_out_path
      srt_t_path = processed_result[video][C.SRT_T]

      print(
          f"==> Adding subtitles to {filename(video)}.mp4 {processed_result[video][C.SIZE]}")

      if not gemini_model:
        # only add one subtitle to the video, using the whisper
        run_ffmpeg_command(
            f"ffmpeg -y -i {processed_result[video][C.TEMP]} -i {processed_result[video][C.SRT]} -map 0:v -map 0:a -map 1 -c:v copy -c:a copy -c:s mov_text -metadata:s:s:0 language={language} {temp_video_out_path}",
            verbose)
      else:
        # translate then add both subtitles, using google
        run_ffmpeg_command(
            f"ffmpeg -y -i {processed_result[video][C.TEMP]} -i {processed_result[video][C.SRT]} -i {srt_t_path} -map 0:v -map 0:a -map 1 -map 2 -c:v copy -c:a copy -c:s mov_text -metadata:s:s:0 language={language} -metadata:s:s:1 language={language_to} {temp_video_out_path}",
            verbose)

    # copy temp files to the output folder
    final_output = os.path.join(
        output_dir, filename(video) + '.mp4')

    print(
        f'==> coping translated video file to output folder: {final_output}')
    shutil.copy(temp_video_out_path, final_output)
    if processed_result[video][C.SRT]:

      print(
          f'==> coping srt file to output folder: {filename(video)+".srt"}')
      shutil.copy(processed_result[video][C.SRT], os.path.join(
          output_dir, filename(video) + '.srt'))
    if processed_result[video][C.SRT_T]:

      print(
          f'==> coping translated srt file to output folder: {filename(video)+"_t.srt"}')
      shutil.copy(processed_result[video][C.SRT_T], os.path.join(
          output_dir, filename(video) + '_t.srt'))
    if processed_result[video][C.AAC]:
      print(
          f'==> coping audio file to output folder: {filename(video)+".aac"}')
      shutil.copy(processed_result[video][C.AAC], os.path.join(
          output_dir, filename(video) + '.aac'))
    processed_result[video][C.END] = time.time()
    processed_result[video][C.DURATION] = format_seconds(
        processed_result[video][C.END] - processed_result[video][C.START])

  # output running summary
  logs = []
  print('\n============== SUMMARY ==============')
  logs.append(["SEQ", "FILE", "SIZE", "DURATION"])
  for i, video in enumerate(to_processed_files):
    size = processed_result[video][C.SIZE][1:len(
        processed_result[video][C.SIZE])-1]
    size = size.split(':')[1].strip()
    logs.append([str(i+1), video, size, processed_result[video][C.DURATION]])
  print(tabulate(logs, headers="firstrow"))
  print('-------------------------------------')


def get_audio(video, processed_result, verbose):

  temp_video_file = processed_result[video][C.TEMP]
  temp_audio_file_out = processed_result[video][C.UUID] + ".aac"
  print(
      f"==> Extracting audio from {filename(video)}.mp4 {processed_result[video][C.SIZE]}")
  audio_output_path = os.path.join(temp_dir, temp_audio_file_out)

  run_ffmpeg_command("ffmpeg -y -i " + temp_video_file +
                     " -vn -acodec copy " + audio_output_path, verbose)

  processed_result[video][C.AAC] = audio_output_path


def get_subtitles(video, processed_result, transcribe: callable):

  temp_aac_file = processed_result[video][C.AAC]
  srt_temp_file = processed_result[video][C.UUID] + '.srt'
  srt_file_temp_path = os.path.join(temp_dir, srt_temp_file)

  print(
      f"==> Generating subtitles for '{filename(video)}.mp4' {processed_result[video][C.SIZE]} This might take a while.")

  warnings.filterwarnings("ignore")
  result = transcribe(temp_aac_file)
  warnings.filterwarnings("default")

  with open(srt_file_temp_path, "w", encoding="utf-8") as srt:
    write_srt(result["segments"], file=srt)

  processed_result[video][C.SRT] = srt_file_temp_path


if __name__ == '__main__':
  main()
