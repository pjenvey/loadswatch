FROM python:3.5.2

RUN apt-get update
RUN apt-get install -y python-pip
RUN pip install docker-py==1.6.0 boto==2.42.0

ADD watch.py watch.py

CMD [ "python", "./watch.py" ]
