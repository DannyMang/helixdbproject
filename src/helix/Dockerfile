FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*


RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN curl -sSL "https://install.helix-db.com" | bash
ENV PATH="/root/.local/bin:${PATH}"
RUN helix install
RUN pip install uv

COPY helix_config/ /app/helix_config/
COPY requirements.txt /app/
COPY *.py /app/

COPY start.sh /start.sh
RUN chmod +x /start.sh
RUN uv pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Stop any existing instances, then deploy
CMD ["/start.sh"]
