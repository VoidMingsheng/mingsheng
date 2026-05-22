# Private Server Deployment

This deploys the interactive static demo only. It does not require Node.js, Python, PostgreSQL, or AI API keys on the server.

## Server Requirements

- Ubuntu 22.04 or newer, Debian, or any Linux server with Docker
- Docker and Docker Compose plugin installed
- A reachable private IP or domain name
- Firewall access to the chosen port, default `8080`

## Deploy

If this PR is merged:

```bash
git clone https://github.com/VoidMingsheng/mingsheng.git
cd mingsheng/hr-interview-intelligence
```

If this PR is not merged yet:

```bash
git clone https://github.com/VoidMingsheng/mingsheng.git
cd mingsheng
git fetch origin codex/hr-interview-intelligence
git checkout codex/hr-interview-intelligence
cd hr-interview-intelligence
```

Start the demo:

```bash
docker compose -f deploy/private-server/docker-compose.demo.yml up -d --build
```

Open:

```text
http://YOUR_SERVER_IP:8080
```

## Update

```bash
git pull
docker compose -f deploy/private-server/docker-compose.demo.yml up -d --build
```

## Stop

```bash
docker compose -f deploy/private-server/docker-compose.demo.yml down
```

## Use A Domain With HTTPS

Put Caddy, Nginx Proxy Manager, Cloudflare Tunnel, Tailscale Funnel, or your existing reverse proxy in front of port `8080`.

Example Caddy reverse proxy:

```caddyfile
hr-demo.example.com {
	reverse_proxy 127.0.0.1:8080
}
```

## Important Limitations

- This is a browser-only demo. Data is saved in each user's browser local storage.
- Do not upload real candidate data to this demo.
- For real HR usage, deploy the full backend/frontend/database stack with authentication, audit logs, encrypted storage, and compliance review.
