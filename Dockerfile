FROM python:3.14-slim

# 1. Install Java 21 (Required for PySpark 4.0+)
RUN apt-get update && apt-get install -y \
    openjdk-21-jre-headless \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Set JAVA_HOME correctly for Debian/Ubuntu
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# 3. Prepare the workspace
WORKDIR /app

# 4. Install Dependencies first (better for Docker caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy the project files
# Note: In docker-compose, we use volumes to sync these live, 
# but we COPY here so the image can also run standalone.
COPY . /app

# 6. Expose the Streamlit port
EXPOSE 8501