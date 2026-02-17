#!/bin/bash

# Employee Verification Platform - Deployment Setup Script
# For Ubuntu 20.04+ VPS

set -e

echo "=========================================="
echo "Employee Verification Platform Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Updating system...${NC}"
apt update && apt upgrade -y

echo -e "${GREEN}Step 2: Installing dependencies...${NC}"
apt install -y python3.11 python3.11-venv python3-pip
apt install -y postgresql postgresql-contrib
apt install -y nginx
apt install -y libpq-dev python3-dev
apt install -y libgl1-mesa-glx libglib2.0-0  # OpenCV dependencies
apt install -y git

echo -e "${GREEN}Step 3: Creating application user...${NC}"
if id "employeeverif" &>/dev/null; then
    echo "User employeeverif already exists"
else
    adduser --disabled-password --gecos "" employeeverif
    usermod -aG www-data employeeverif
fi

echo -e "${GREEN}Step 4: Setting up PostgreSQL...${NC}"
read -p "Enter database name [employee_verification]: " DB_NAME
DB_NAME=${DB_NAME:-employee_verification}

read -p "Enter database user [employeeverif]: " DB_USER
DB_USER=${DB_USER:-employeeverif}

read -sp "Enter database password: " DB_PASSWORD
echo ""

# Create PostgreSQL database and user
sudo -u postgres psql <<EOF
CREATE DATABASE ${DB_NAME};
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
ALTER ROLE ${DB_USER} SET client_encoding TO 'utf8';
ALTER ROLE ${DB_USER} SET default_transaction_isolation TO 'read committed';
ALTER ROLE ${DB_USER} SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF

echo -e "${GREEN}Database created successfully${NC}"

echo -e "${GREEN}Step 5: Project setup...${NC}"
PROJECT_DIR="/home/employeeverif/employee_verification_platform"

if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}Project directory already exists${NC}"
else
    echo "Please upload your project files to: $PROJECT_DIR"
    echo "Then run this script again"
    exit 0
fi

cd $PROJECT_DIR

echo -e "${GREEN}Step 6: Creating virtual environment...${NC}"
sudo -u employeeverif python3.11 -m venv venv
sudo -u employeeverif bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u employeeverif bash -c "source venv/bin/activate && pip install -r requirements.txt"
sudo -u employeeverif bash -c "source venv/bin/activate && pip install gunicorn"

echo -e "${GREEN}Step 7: Configuring environment...${NC}"
read -p "Enter your domain name (or IP address): " DOMAIN_NAME

# Generate secret key
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Create .env file
sudo -u employeeverif bash -c "cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${DOMAIN_NAME}

DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=${DB_NAME}
DATABASE_USER=${DB_USER}
DATABASE_PASSWORD=${DB_PASSWORD}
DATABASE_HOST=localhost
DATABASE_PORT=5432

SIMILARITY_THRESHOLD=0.65
MAX_UPLOAD_SIZE=5242880
CHROMA_PERSIST_DIRECTORY=${PROJECT_DIR}/chroma_db
EOF"

echo -e "${GREEN}Step 8: Running Django migrations...${NC}"
sudo -u employeeverif bash -c "cd $PROJECT_DIR && source venv/bin/activate && python manage.py makemigrations"
sudo -u employeeverif bash -c "cd $PROJECT_DIR && source venv/bin/activate && python manage.py migrate"

echo -e "${GREEN}Step 9: Creating superuser...${NC}"
echo "Please create a Django superuser:"
sudo -u employeeverif bash -c "cd $PROJECT_DIR && source venv/bin/activate && python manage.py createsuperuser"

echo -e "${GREEN}Step 10: Collecting static files...${NC}"
sudo -u employeeverif bash -c "cd $PROJECT_DIR && source venv/bin/activate && python manage.py collectstatic --noinput"

echo -e "${GREEN}Step 11: Creating directories...${NC}"
sudo -u employeeverif mkdir -p ${PROJECT_DIR}/media/employee_photos
sudo -u employeeverif mkdir -p ${PROJECT_DIR}/media/temp
sudo -u employeeverif mkdir -p ${PROJECT_DIR}/chroma_db
chmod 755 ${PROJECT_DIR}/media
chmod 755 ${PROJECT_DIR}/chroma_db

echo -e "${GREEN}Step 12: Setting up Gunicorn service...${NC}"
cat > /etc/systemd/system/gunicorn.service << EOF
[Unit]
Description=Gunicorn daemon for Employee Verification Platform
After=network.target

[Service]
User=employeeverif
Group=www-data
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${PROJECT_DIR}/venv/bin"
ExecStart=${PROJECT_DIR}/venv/bin/gunicorn \\
          --workers 3 \\
          --bind unix:${PROJECT_DIR}/gunicorn.sock \\
          config.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

systemctl start gunicorn
systemctl enable gunicorn

echo -e "${GREEN}Step 13: Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/employee_verification << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    client_max_body_size 10M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias ${PROJECT_DIR}/staticfiles/;
    }
    
    location /media/ {
        alias ${PROJECT_DIR}/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:${PROJECT_DIR}/gunicorn.sock;
    }
}
EOF

ln -sf /etc/nginx/sites-available/employee_verification /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

echo -e "${GREEN}Step 14: Configuring firewall...${NC}"
ufw allow 'Nginx Full'
ufw allow OpenSSH
echo "y" | ufw enable

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Your application is now running at:"
echo "http://${DOMAIN_NAME}"
echo ""
echo "Admin panel: http://${DOMAIN_NAME}/admin/"
echo ""
echo "To enable HTTPS (recommended), run:"
echo "  apt install certbot python3-certbot-nginx"
echo "  certbot --nginx -d ${DOMAIN_NAME}"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status gunicorn"
echo "  sudo systemctl restart gunicorn"
echo "  sudo systemctl restart nginx"
echo "  sudo journalctl -u gunicorn -f"
echo ""
echo "Logs location:"
echo "  Gunicorn: sudo journalctl -u gunicorn"
echo "  Nginx: /var/log/nginx/error.log"
echo ""
