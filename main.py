import math
import ffmpeg

from faster_whisper import WhisperModel
from fastapi import FastAPI, File, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import UploadFile
from fastapi.responses import RedirectResponse
from fastapi import Request
from fastapi.responses import StreamingResponse
import cv2
import subprocess

input_video = "input.mp4"
input_video_name = input_video.replace(".mp4", "")
CHUNK_SIZE = 1024 * 1024
templates = Jinja2Templates(directory='templates')

app = FastAPI()


@app.get('/', response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.post('/upload')
def uploadMp4_video(file: UploadFile = File(...)):
    file_data = file.file

    with open("input.mp4", "wb+") as f:
        f.write(file_data.read())

    extracted_audio = extract_audio(input_video)
    language, segments = transcribe(audio=extracted_audio)
    subtitle_file = generate_subtitle_file(
        language=language,
        segments=segments
    )
    subtitle_color = "yellow"
    overwrite= True
    add_subtitle_to_video(input_video, subtitle_file, subtitle_color, overwrite)
    redirect_url = "http://localhost:8000/output"
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/video")
async def video_endpoint():
    def iterfile():
        with open("output-input.mp4", mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="video/mp4")


@app.get("/output")
async def read_root(request: Request):
    return templates.TemplateResponse("video.html", context={"request": request})


def extract_audio(input_video):
    extracted_audio = f"audio-{input_video.replace(".mp4", "")}.wav"
    stream = ffmpeg.input(input_video)
    stream = ffmpeg.output(stream, extracted_audio)
    ffmpeg.run(stream, overwrite_output=True)
    return extracted_audio


def transcribe(audio):
    model = WhisperModel("small")
    segments, info = model.transcribe(audio)
    language = info[0]
    print("Transcription language", info[0])
    segments = list(segments)
    for segment in segments:
        # print(segment)
        print("[%.2fs -> %.2fs] %s" %
              (segment.start, segment.end, segment.text))
    return language, segments


def format_time(seconds):
    hours = math.floor(seconds / 3600)
    seconds %= 3600
    minutes = math.floor(seconds / 60)
    seconds %= 60
    milliseconds = round((seconds - math.floor(seconds)) * 1000)
    seconds = math.floor(seconds)
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:01d},{milliseconds:03d}"

    return formatted_time


def generate_subtitle_file(language, segments):
    subtitle_file = f"sub-{input_video_name}.{language}.srt"
    text = ""
    for index, segment in enumerate(segments):
        segment_start = format_time(segment.start)
        segment_end = format_time(segment.end)
        text += f"{str(index + 1)} \n"
        text += f"{segment_start} --> {segment_end} \n"
        text += f"{segment.text} \n"
        text += "\n"

    f = open(subtitle_file, "w")
    f.write(text)
    f.close()

    return subtitle_file


def check_subtitles(video_path):
    video = cv2.VideoCapture(video_path)
    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break
        subtitles_present = True

        if subtitles_present:
            print("Subtitles found in the video.")
            break

    video.release()


def add_subtitle_to_video(video_path, subtitle_path, subtitle_color="yellow", overwrite=True):
    output_path = f"output-{input_video_name}.mp4"
    output_format = "mp4"

    # Command to add subtitles using ffmpeg
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', f"subtitles='{subtitle_path}':force_style='Fontcolor={subtitle_color}'",
        '-y' if overwrite else '',  # Add '-y' option to overwrite the output file if overwrite is True
        '-f', output_format,  # Specify the output format
        output_path
    ]
    subprocess.run(ffmpeg_cmd)
    return output_path
