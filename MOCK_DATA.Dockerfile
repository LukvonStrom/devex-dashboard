FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make the entrypoint script executable
RUN chmod +x /app/mock-entrypoint.sh

# Expose Streamlit's default port
EXPOSE 8501

# Set the entrypoint script
ENTRYPOINT ["/app/mock-entrypoint.sh"]