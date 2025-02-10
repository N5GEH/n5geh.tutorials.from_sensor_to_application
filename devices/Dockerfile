# syntax=docker/dockerfile:1

FROM python:3.9-slim
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade remi

COPY ./figures /app/figures
COPY ./SimulationModel.py /app/SimulationModel.py
COPY ./simulation.py /app/simulation.py
EXPOSE 8000

CMD [ "python", "./simulation.py" ]