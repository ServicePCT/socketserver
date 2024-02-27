FROM python:3.10
RUN apt update
RUN apt install iputils-ping -y
RUN apt install nano -y
RUN apt install traceroute -y
RUN apt install ffmpeg -y
RUN pip install --upgrade pip
RUN pip install pika
RUN pip install requests

WORKDIR /app

ADD /Thread/chat_assistent/autoresponder_detect/requirements.txt requirements.txt
RUN pip install -r ./requirements.txt
RUN rm ./requirements.txt
