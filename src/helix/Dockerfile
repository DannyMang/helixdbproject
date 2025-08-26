FROM python:3.9

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

COPY helix_config/ /app/helix_config/
COPY /*.py /app/

COPY start.sh /start.sh
RUN chmod +x /start.sh

# Stop any existing instances, then deploy
CMD ["/start.sh"]
