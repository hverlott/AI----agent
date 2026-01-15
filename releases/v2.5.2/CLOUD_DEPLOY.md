# Cloud Server Deployment Guide

This guide describes how to deploy the SaaS AI System on a cloud server (AWS, DigitalOcean, Alibaba Cloud, etc.).

**Recommended Approach: Docker Deployment**

Using Docker is the superior choice for cloud environments because:
1.  **Consistency**: Eliminates "it works on my machine" issues.
2.  **Dependencies**: Automatically handles complex installations like `pgvector`.
3.  **Maintenance**: Easy to update and back up.
4.  **Isolation**: Keeps your server clean.

## Prerequisites

1.  A cloud server (Ubuntu 20.04/22.04 LTS recommended).
2.  Root or sudo access.
3.  Git (optional, for cloning code).

## Step 1: Install Docker & Docker Compose

Run the following commands on your server:

```bash
# Update package list
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose Plugin (if not included)
sudo apt-get install -y docker-compose-plugin
```

## Step 2: Upload Files

Upload the `releases/v2.5.2` folder to your server (e.g., `/opt/saas-ai`). You can use `scp`, `rsync`, or an FTP client like FileZilla.

```bash
# Example using scp
scp -r releases/v2.5.2 user@your-server-ip:/opt/saas-ai
```

## Step 3: Configure Environment

1.  Navigate to the directory:
    ```bash
    cd /opt/saas-ai
    ```
2.  (Optional) Edit `docker-compose.yml` if you need to change passwords or ports.
3.  Ensure your `config.txt` and other configuration files are set up correctly.

## Step 4: Start the System

Run the following command to build and start the services:

```bash
sudo docker compose up -d --build
```

- `-d`: Run in detached mode (background).
- `--build`: Force rebuild of the Docker image.

## Step 5: Verify Deployment

1.  **Check Status**:
    ```bash
    sudo docker compose ps
    ```
    You should see `saas_app` and `saas_postgres` running.

2.  **View Logs**:
    ```bash
    sudo docker compose logs -f app
    ```

3.  **Access Admin Panel**:
    Open your browser and visit: `http://<your-server-ip>:8501`

## Maintenance

- **Stop System**: `sudo docker compose down`
- **Restart System**: `sudo docker compose restart`
- **Update Code**: Upload new files and run `sudo docker compose up -d --build`.
- **Backup Database**:
    ```bash
    # Backup to a file on the host
    sudo docker exec -t saas_postgres pg_dumpall -c -U postgres > dump_$(date +%Y-%m-%d).sql
    ```

## Troubleshooting

- **Database Connection Error**: Ensure the `postgres` service is healthy before `app` starts. The `docker-compose.yml` already includes a health check.
- **Port Conflicts**: If port 80/443/5432 is taken, edit `docker-compose.yml` to map to different host ports.
