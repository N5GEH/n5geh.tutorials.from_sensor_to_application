# syntax=docker/dockerfile:1

# stage 0
FROM alpine/git
WORKDIR /app
RUN git clone https://github.com/RWTH-EBC/FiLiP.git

# stage 1
FROM python:3.9-slim
WORKDIR /app
COPY --from=0 /app/FiLiP /app/FiLiP
RUN pip install -e /app/FiLiP
COPY ./* /app/
EXPOSE 5000

CMD [ "python", "./socket2mqtt.py" ]
