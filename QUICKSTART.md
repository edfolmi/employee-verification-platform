# Quick Start Guide

## Development Setup (5 minutes)

### 1. Prerequisites
```bash
python3.11 --version  # Verify Python 3.11+ installed
```

### 2. Setup
```bash
cd employee_verification_platform

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed (defaults work for development)

# Setup database
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Create directories
mkdir -p media/employee_photos media/temp chroma_db

# Run server
python manage.py runserver
```

### 3. Access
- **Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin

## Production Deployment (Ubuntu VPS)

### Option 1: Automated Deployment
```bash
# On your VPS as root:
cd /path/to/project
chmod +x deploy.sh
sudo ./deploy.sh
```

### Option 2: Manual Deployment
Follow the detailed steps in `README.md` under "Deployment on VPS (Ubuntu)"

## Testing the System

### Add First Employee
1. Go to http://localhost:8000
2. Click "Add Employee"
3. Fill in details:
   - Name: John Doe
   - Phone: +1234567890
   - Email: john@example.com
   - Employer: Tech Corp
   - Position: Software Engineer
   - Reputation: 8.5
   - Upload a clear face photo
4. Submit

### Verify Employee
1. Click "Verify Employee"
2. Upload a photo of the same person (can be different photo)
3. Click "Verify Identity"
4. See the match result!

## Similarity Threshold Explained

The threshold determines matching strictness:
- **0.60-0.65**: Lenient (may match similar faces)
- **0.65-0.70**: Balanced (recommended)
- **0.70-0.80**: Strict (requires high similarity)

Configure in `.env`:
```env
SIMILARITY_THRESHOLD=0.65
```

## Common Commands

### Development
```bash
# Run server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Django shell
python manage.py shell
```

### Production
```bash
# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx

# View logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting Quick Fixes

### "No face detected"
- Use well-lit, front-facing photos
- Ensure only one face in photo
- Try different angle

### Import errors
```bash
pip install -r requirements.txt
```

### Database errors
```bash
python manage.py migrate
```

### Static files not loading
```bash
python manage.py collectstatic --noinput
```

### ChromaDB errors
```bash
mkdir -p chroma_db
chmod 755 chroma_db
```

## Next Steps

1. ✅ Add test employees
2. ✅ Test verification with different photos
3. ✅ Adjust similarity threshold if needed
4. ✅ Deploy to production
5. ✅ Enable HTTPS with Let's Encrypt
6. ✅ Set up backups

## Support

For detailed documentation, see `README.md`
For deployment details, see deployment section in `README.md`
