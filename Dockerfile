FROM python:3.12-slim-bullseye AS base
COPY requirements.txt .
RUN export PATH=$PATH:/root/.local/bin
RUN pip3 install -r requirements.txt 

COPY *.py /
COPY run.sh /

ENTRYPOINT ["/run.sh"]
