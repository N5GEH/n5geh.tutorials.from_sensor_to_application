# syntax=docker/dockerfile:1

FROM python:3.9-slim
WORKDIR /app

RUN pip install PySimpleGUIWeb && pip install --upgrade remi && pip install numpy
COPY ./figures /app/figures
COPY ./SimulationModel.py /app/SimulationModel.py
COPY ./simulation.py /app/simulation.py
EXPOSE 8000

CMD [ "python", "./simulation.py" ]