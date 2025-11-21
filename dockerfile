FROM python:3.13-slim-bookworm
WORKDIR /app

RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/RoxBlox3/neuro-schedule .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3000

CMD ["python", "discordtocalendar.py"]