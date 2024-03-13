# Use an official Python runtime as a parent image (slim variant for smaller size)
FROM python:3.9-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /usr/src/app

# Install dependencies needed for psycopg2 binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build dependencies
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY ./requirements.txt /usr/src/app/requirements.txt

# Install project dependencies
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

# Use a new stage to discard the build context and reduce image size
FROM python:3.9-slim

WORKDIR /usr/src/app

# Copy only the dependencies installation from the 1st stage
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .

# Install dependencies
RUN pip install --no-cache /wheels/*

# Copy the rest of the application
COPY . /usr/src/app/

