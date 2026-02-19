FROM python:3.11-bullseye

WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Bootstrap pip + setuptools + wheel
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

# Copy and install requirements
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app", "--workers", "3"]
