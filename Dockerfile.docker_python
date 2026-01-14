FROM python:3.11-slim

WORKDIR /app

# Installer dépendances système pour numpy/scipy
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        && \
    rm -rf /var/lib/apt/lists/*

# Copier et installer les requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copier le modèle et l'app
COPY models/ ./models/
COPY app.py .

# Créer utilisateur non-root
RUN useradd -m -u 1000 mluser && \
    chown -R mluser:mluser /app
USER mluser

EXPOSE 8080

# Utiliser gunicorn en production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]