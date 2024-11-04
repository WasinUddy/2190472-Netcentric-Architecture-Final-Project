FROM python:3.12-slim

# Set working directory
WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code
RUN mkdir /app/src

COPY src /app/src
COPY server.py .

# Expose port 1000 & 1001
EXPOSE 1000
EXPOSE 1001

# Run the application
CMD ["python", "server.py"]

