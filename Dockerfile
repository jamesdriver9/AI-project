
FROM python:3.14-slim

# 1. Install Java 21 (The new standard for 2026)
RUN apt-get update && apt-get install -y \
    openjdk-21-jre-headless \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Set JAVA_HOME (Updated for Java 21)
# Note: The path changes from '17' to '21'
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

# 3. Install PySpark and high-performance data tools
RUN pip install --no-cache-dir \
    pyspark \
    pandas \
    pyarrow \
    langchain \
    langgraph

# 4. Set the working directory and copy your code
WORKDIR /app
COPY . /app

# Run your agent
CMD ["python", "main.py"]