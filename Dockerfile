FROM python:3.10

# Install node.js 18
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get update && apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app
RUN pip install --no-cache-dir /app

ENTRYPOINT ["uvicorn", "governedrunner.main:app"]
