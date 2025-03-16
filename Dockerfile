FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "Developer_Experience_Dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]