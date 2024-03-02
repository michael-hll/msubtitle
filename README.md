# mSubtitle

### Add sub-title to your video automatically.

It will default use OpenAI Whisper to get your video's audio and then translate to the target language.

But the whisper's tranlsation is not good at this moment, so you can choose Google gemini api to translate the srt file.

## Options 1 => OpenAI Whisper

### run command like below: add Chinese subtitle to your video

`$ python autosubtitle.py your-video.mp4 --model large --task transcribe --language zh`

This command will generate three files: your-video.aac, your-video.srt, your-video_out.mp4

## Options 2 => OpenAI Whisper & Google Gemini

### run command like below: add both English subtitle and Chinese to your video

`$ python autosubtitle.py your-video.mp4 --model large --task transcribe --language en --gemini_model gemini-pro --language_to zh`

This command will generate four files: your-video.aac, your-video.srt, your-video_t.srt, your-video_out.mp4

The key to enable Google Gemini here is to use the --gemini_model parameter, and the program will translate the generated srt file of language (--language) to target language (--language_to)

## Steps to use it:

1. Clone it to your local;
2. Install FFmpeg on Mac OS (didn't test on windows): `brew install ffmpeg`
3. Start a python env with python 3.11.\* or later, then inside your python env install the followings:
   1. pip install openai-whisper
   2. pip install -q -U google-generativeai
   3. pip install python-dotenv
4. You can also use the pip install the requirements.txt instead of step 3:
   1. `pip install -r requirements.txt`

For more parameters, see the help:

`python autosubtitle.py -h`

And also good to see whisper's document on the parameters usage.
