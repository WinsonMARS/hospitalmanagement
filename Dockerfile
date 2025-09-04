FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Install pytz for timezone handling
RUN pip install --no-cache-dir pytz

COPY . .

# Apply the UTC patch before running any commands
COPY patch_utc_check.py .
ENV PYTHONPATH=/app:$PYTHONPATH

EXPOSE 8000

# Use our patched runner instead of manage.py
CMD ["sh", "-c", "python run_with_patch.py migrate && python run_with_patch.py runserver 0.0.0.0:8000"]