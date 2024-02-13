FROM python:3.12
RUN apt update
RUN apt install iputils-ping -y
RUN apt install traceroute -y
RUN pip install --upgrade pip
RUN pip install librosa -y
RUN pip install soundfile -y
RUN pip install resampy -y
RUN pip install numpy -y
RUN pip install pydub -y
RUN pip install pickle -y

WORKDIR app