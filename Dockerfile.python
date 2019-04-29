FROM python:3.7-alpine

ARG sparkplug_wheel

ADD requirements.txt .
ADD requirements-dev.txt .
ADD dist/$sparkplug_wheel .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r requirements-dev.txt
RUN pip install nose
RUN pip install $sparkplug_wheel

ENV PYTHONPATH /app/
