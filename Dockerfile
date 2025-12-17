FROM python:3.13-slim
LABEL authors="Amir"

#Set env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

#Set workdir
WORKDIR /app

# build argument (provider)
ARG INSTAGRAM_PROVIDER
ENV INSTAGRAM_PROVIDER=$INSTAGRAM_PROVIDER

# Copy requirements
COPY requirements ./requirements

# Install dependencies based on provider
RUN echo "Installing provider: $INSTAGRAM_PROVIDER" && \
    if [ "$INSTAGRAM_PROVIDER" = "instagrapi" ]; then \
        pip install --no-cache-dir -r requirements/instagrapi.txt; \
    else \
        echo "Unknown INSTAGRAM_PROVIDER: $INSTAGRAM_PROVIDER" && exit 1; \
    fi

# Copy project source
COPY . .