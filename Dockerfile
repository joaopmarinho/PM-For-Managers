FROM python:3.11-slim

LABEL maintainer="João Pedro Marinho"
LABEL description="Process Mining Multidimensional Dashboard"

WORKDIR /app

# Install deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Ensure the database directory exists inside the image
RUN mkdir -p /app/database

# Environment defaults (can be overridden by docker-compose)
ENV DB_PATH=/app/database/storage.db \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
