FROM python:3.10
RUN apt update
RUN apt install iputils-ping -y
RUN apt install nano -y
RUN apt install traceroute -y
RUN apt install ffmpeg -y
RUN pip install --upgrade pip
RUN pip install librosa
RUN pip install soundfile
RUN pip install resampy
RUN pip install numpy
RUN pip install pydub
RUN pip install pika
RUN pip install requests
RUN #pip install pickle

WORKDIR app
