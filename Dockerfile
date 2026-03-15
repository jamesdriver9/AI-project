FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for Matplotlib and OS interactions)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project
COPY . .

# Create the data directory if it doesn't exist
RUN mkdir -p data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the agent
CMD ["python", "main.py"]