curl -sSL https://install.helix-db.com | bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
source ~/.bashrc
helix install
helix update
helix deploy --path /src/helix/helix_config

docker compose up --build

tail -f /dev/null
