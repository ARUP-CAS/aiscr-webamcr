FROM python:3.8
ENV PYTHONUNBUFFERED=1
RUN mkdir /code
WORKDIR /code
COPY . /code/
RUN pip install -r /code/webclient/requirements/dev.txt
