FROM python:3.13-slim-bookworm
WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt
COPY discordtocalendar.py ./discordtocalendar.py
COPY pytest.ini ./pytest.ini

CMD ["python", "discordtocalendar.py"]