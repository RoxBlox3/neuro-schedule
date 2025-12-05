FROM python:3.13-slim-bookworm
WORKDIR /app

COPY requirements.txt .
# RUN apt-get update && apt-get install -y git
# RUN git clone https://github.com/RoxBlox3/neuro-schedule .

RUN python -m pip install --no-cache-dir -r requirements.txt
COPY discordtocalendar.py ./discordtocalendar.py

CMD ["python", "discordtocalendar.py"]