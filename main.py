import moviepy.editor as mp
import speech_recognition as sr
from fastapi import FastAPI, Form, Request, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import UploadFile
import os

app = FastAPI()
templates = Jinja2Templates(directory='templates')


@app.post('/upload')
def uploadMp4_video(file: UploadFile = File(...)):
    file_name = file.filename
    mime_type = file.content_type
    file_data = file.file
    temp_filepath = "temp.mp4"

    print(f'file name :{file_name} and mime_type : {mime_type}')
    with open(temp_filepath, "wb") as f:
        f.write(file_data.read())

    video = mp.VideoFileClip(temp_filepath)
    audio_file = video.audio
    audio_file.write_audiofile("temp.wav")
    r = sr.Recognizer()
    with sr.AudioFile("temp.wav") as source:
        data = r.record(source)
        text = r.recognize_google(data)

    os.remove(temp_filepath)
    os.remove("temp.wav")
    return text


@app.get('/', response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.post('/test')
def test(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})
