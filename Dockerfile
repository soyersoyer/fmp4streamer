# syntax=docker/Dockerfile:1
FROM python:3.10.5-alpine
ARG PORT=8000
WORKDIR /usr/local/src/fmp4streamer
COPY . .
ENTRYPOINT [ "python3", "fmp4streamer.py" ]
EXPOSE $PORT
