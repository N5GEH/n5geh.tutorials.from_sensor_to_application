# syntax=docker/dockerfile:1
FROM python:3.9-slim
WORKDIR /app
RUN pip install -U filip==0.4.1
COPY ./* /app/
EXPOSE 5000

CMD [ "python", "./socket2mqtt.py" ]
