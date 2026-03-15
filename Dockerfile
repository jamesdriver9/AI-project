
FROM python:3.14-slim

# 1. Install Java 21
RUN apt-get update && apt-get install -y \
    openjdk-21-jre-headless \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

WORKDIR /app

# 3. Use the requirements file (The "Pro" way)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of your code
COPY . /app

CMD ["python", "main.py"]