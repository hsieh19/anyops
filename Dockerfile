# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Install necessary Ansible collections for Huawei, Cisco, H3C, Ruijie
RUN ansible-galaxy collection install \
    ansible.netcommon \
    community.network \
    cisco.ios \
    h3c.comware \
    ruijie.networks \
    && rm -rf /root/.ansible/galaxy/cache

# Stage 2: Final stage (Runtime)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Only install runtime dependencies (SSH client is necessary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sshpass \
    openssh-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /root/.ansible /root/.ansible

# Ensure paths are correct
ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
