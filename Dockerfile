FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies for Ansible and SSH
RUN apt-get update && apt-get install -y --no-install-recommends \
    sshpass \
    openssh-client \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Ansible Galaxy collections for Network vendors
# These are essential for Huawei (community.network), Cisco (cisco.ios), etc.
RUN ansible-galaxy collection install ansible.netcommon community.network cisco.ios

# Copy project files (will be overridden by volume in dev)
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Start Gunicorn or Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
