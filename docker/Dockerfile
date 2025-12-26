FROM python:3.10-slim-buster

# Install Node.js 18
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# Install system dependencies
RUN apt-get install -y git

WORKDIR /app

# Install Python dependencies
# Utilizing a cache mount would be ideal in production, but keeping it simple here
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# We assume the code is mounted at runtime to /app
# We assume the Gemini CLI is mounted or available in PATH

ENTRYPOINT ["python3", "optimizer/optimize.py"]
