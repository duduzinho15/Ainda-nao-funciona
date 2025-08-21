# Dockerfile para Garimpeiro Geek
# Multi-stage build para otimização

# Stage 1: Base com dependências
FROM python:3.11-slim as base

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro para cache de layers
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Dependências de ML
FROM base as ml-deps

# Instalar dependências para ML
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scikit-learn \
    scipy \
    matplotlib \
    seaborn

# Stage 3: Dependências de produção
FROM base as prod-deps

# Instalar dependências de produção
RUN pip install --no-cache-dir \
    gunicorn \
    uvicorn \
    fastapi \
    psycopg2-binary \
    redis \
    celery \
    flower

# Stage 4: Aplicação
FROM prod-deps as app

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/.data /app/logs /app/backups && \
    chown -R app:app /app

# Mudar para usuário não-root
USER app

# Expor portas
EXPOSE 8080 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando padrão
CMD ["python", "main.py"]

# Stage 5: Desenvolvimento (opcional)
FROM base as dev

# Instalar ferramentas de desenvolvimento
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    black \
    flake8 \
    mypy \
    ipython \
    jupyter

# Copiar código
COPY . .

# Expor porta de desenvolvimento
EXPOSE 8080 8081 8888

# Comando de desenvolvimento
CMD ["python", "-m", "app.dashboard", "--dev"]
