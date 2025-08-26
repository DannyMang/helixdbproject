FROM python:3.9

WORKDIR /code

RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY fastapi/requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN curl -sSL "https://install.helix-db.com" | bash
ENV PATH="/root/.local/bin:${PATH}"
RUN helix install

COPY helix_config/ ./

RUN helix deploy

CMD ["sh", "-c", "helix deploy", "--path", "/helix_config"]
