FROM python:3.13-slim

WORKDIR /app

# Install dependencies for Selenium and Chrome
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_EXECUTABLE_PATH=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

COPY pyproject.toml .
RUN pip install .

COPY . .

ENV PYTHONPATH=/app
