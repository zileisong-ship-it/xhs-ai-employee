FROM python:3.12-slim

# System dependencies for OpenCV (used by file_parser.py for video frame extraction)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd -m -s /bin/bash streamlit

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=streamlit:streamlit . .

# Create writable data directories
RUN mkdir -p /app/data/media /app/data/skills \
    && chown -R streamlit:streamlit /app/data

USER streamlit

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -sf http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.address=0.0.0.0", \
    "--server.port=8501", \
    "--server.enableCORS=false", \
    "--server.enableXsrfProtection=true", \
    "--browser.gatherUsageStats=false"]
