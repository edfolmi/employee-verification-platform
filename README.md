# Employee Verification Platform

A production-ready facial recognition employee verification platform built with Django, DeepFace (ArcFace model), and ChromaDB for vector similarity search.

## 🎯 Features

- **Employee Registration**: Add employees with personal details, photos, and reputation scores
- **Facial Recognition**: Extract and store facial embeddings using DeepFace with ArcFace model
- **Identity Verification**: Upload a photo to verify employee identity using cosine similarity
- **Vector Search**: ChromaDB for efficient facial embedding storage and retrieval
- **Clean Architecture**: Modular service layer separating business logic from views
- **Production Ready**: Secure settings, error handling, and deployment configurations

## 🏗️ Technology Stack

- **Backend**: Django 5.0.2
- **Database**: PostgreSQL (production) / SQLite (development)
- **Face Recognition**: DeepFace 0.0.92 with ArcFace model
- **Face Detection**: RetinaFace backend
- **Vector Database**: ChromaDB 0.4.24
- **Frontend**: Django Templates + Bootstrap 5
- **Python**: 3.11+

## 📁 Project Structure

```
employee_verification_platform/
├── config/                      # Django project settings
│   ├── __init__.py
│   ├── settings.py             # Main settings
│   ├── urls.py                 # Root URL configuration
│   └── wsgi.py                 # WSGI application
├── employees/                   # Main Django app
│   ├── migrations/             # Database migrations
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── face_service.py    # DeepFace operations
│   │   └── chroma_service.py  # ChromaDB operations
│   ├── static/                 # Static files
│   │   └── css/
│   │       └── style.css
│   ├── templates/              # HTML templates
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── add_employee.html
│   │   ├── verify_employee.html
│   │   ├── result.html
│   │   └── employee_list.html
│   ├── templatetags/           # Custom template filters
│   │   ├── __init__.py
│   │   └── custom_filters.py
│   ├── __init__.py
│   ├── admin.py               # Admin interface
│   ├── apps.py                # App configuration
│   ├── forms.py               # Django forms
│   ├── models.py              # Database models
│   ├── urls.py                # App URLs
│   └── views.py               # View controllers
├── .env.example               # Environment variables template
├── .gitignore
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Quick Start (Development)

### Prerequisites

- Python 3.11 or higher
- pip
- Virtual environment tool (venv)
- PostgreSQL (optional, SQLite works for development)

### Installation Steps

1. **Clone or download the project**

```bash
cd employee_verification_platform
```

2. **Create and activate virtual environment**

```bash
# Linux/Mac
python3.11 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- Django and related packages
- DeepFace and TensorFlow dependencies
- ChromaDB
- OpenCV and image processing libraries

4. **Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env` and configure as needed. For development with SQLite:

```env
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# SQLite for development
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3

SIMILARITY_THRESHOLD=0.65
MAX_UPLOAD_SIZE=5242880
CHROMA_PERSIST_DIRECTORY=chroma_db
```

5. **Run migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

7. **Create required directories**

```bash
mkdir -p media/employee_photos media/temp
mkdir -p chroma_db
```

8. **Collect static files**

```bash
python manage.py collectstatic --noinput
```

9. **Run development server**

```bash
python manage.py runserver
```

Visit: http://localhost:8000

## 🔧 Configuration

### Similarity Threshold

The similarity threshold determines how strict the facial matching is:

- **0.5-0.6**: Very lenient (may have false positives)
- **0.65-0.7**: Balanced (recommended)
- **0.75-0.85**: Strict (may miss valid matches)
- **0.9+**: Very strict (requires near-perfect match)

Configure in `.env`:
```env
SIMILARITY_THRESHOLD=0.65
```

### How Similarity Works

1. **Embedding Extraction**: DeepFace extracts a 512-dimensional vector from each face
2. **Normalization**: Vectors are normalized for cosine similarity
3. **Cosine Similarity**: Measures angle between vectors (0-1, where 1 is identical)
4. **Distance to Similarity**: ChromaDB returns distance; we convert to similarity: `1 - (distance / 2)`
5. **Threshold Check**: If similarity ≥ threshold, it's a match

Example:
- Distance: 0.5 → Similarity: 0.75 (75%)
- Distance: 0.7 → Similarity: 0.65 (65%)
- Distance: 1.0 → Similarity: 0.50 (50%)

### Database Configuration

#### PostgreSQL (Production)

In `.env`:
```env
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=employee_verification
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

#### SQLite (Development)

In `.env`:
```env
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3
```

## 🎨 Usage

### Adding an Employee

1. Navigate to **Add Employee**
2. Fill in employee details:
   - Full Name
   - Phone
   - Email
   - Employer Name
   - Position
   - Reputation Score (0-10)
   - Notes (optional)
   - Photo (required - must contain exactly one face)
3. Click **Add Employee**
4. System will:
   - Validate the image
   - Extract facial embedding
   - Store in both Django DB and ChromaDB
   - Show success message

### Verifying an Employee

1. Navigate to **Verify Employee**
2. Upload a photo (doesn't need to be identical to registered photo)
3. Click **Verify Identity**
4. System will:
   - Extract embedding from uploaded photo
   - Search ChromaDB for closest match
   - Calculate similarity score
   - Return employee details if match found (≥ threshold)

### Understanding Results

**Match Found:**
- Employee details displayed
- Similarity percentage shown
- Confidence level (High/Medium)
- Reputation score highlighted

**No Match:**
- Friendly message displayed
- Closest similarity shown (if any)
- Suggestions to try again or register

## 🔐 Security Considerations

### Implemented Security Features

1. **CSRF Protection**: Enabled on all forms
2. **File Upload Validation**: 
   - Type checking (JPEG, PNG, WebP only)
   - Size limits (5MB default)
3. **SQL Injection Protection**: Django ORM prevents SQL injection
4. **XSS Protection**: Django templates auto-escape content
5. **Secure Headers**: Configured in production mode
6. **Environment Variables**: Sensitive data in `.env` file

### Production Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure HTTPS (SSL/TLS)
- [ ] Set proper `ALLOWED_HOSTS`
- [ ] Use PostgreSQL (not SQLite)
- [ ] Regular security updates
- [ ] Implement rate limiting
- [ ] Set up proper file permissions
- [ ] Use environment variables for secrets
- [ ] Enable Django security middleware

## 🚢 Deployment on VPS (Ubuntu)

### Prerequisites

- Ubuntu 20.04+ VPS (DigitalOcean, Linode, etc.)
- Domain name (optional but recommended)
- SSH access to server

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y nginx
sudo apt install -y libpq-dev python3-dev
sudo apt install -y libgl1-mesa-glx libglib2.0-0  # OpenCV dependencies
```

### Step 2: PostgreSQL Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE employee_verification;
CREATE USER your_db_user WITH PASSWORD 'strong_password_here';
ALTER ROLE your_db_user SET client_encoding TO 'utf8';
ALTER ROLE your_db_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE your_db_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE employee_verification TO your_db_user;
\q
```

### Step 3: Project Setup

```bash
# Create project user
sudo adduser employeeverif
sudo usermod -aG sudo employeeverif
su - employeeverif

# Clone/upload project
cd /home/employeeverif
# Upload your project files here

cd employee_verification_platform

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### Step 4: Environment Configuration

```bash
# Create production .env
nano .env
```

Add:
```env
SECRET_KEY=generate-a-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-server-ip

DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=employee_verification
DATABASE_USER=your_db_user
DATABASE_PASSWORD=strong_password_here
DATABASE_HOST=localhost
DATABASE_PORT=5432

SIMILARITY_THRESHOLD=0.65
MAX_UPLOAD_SIZE=5242880
CHROMA_PERSIST_DIRECTORY=/home/employeeverif/employee_verification_platform/chroma_db
```

### Step 5: Django Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Create directories
mkdir -p media/employee_photos media/temp
mkdir -p chroma_db

# Set permissions
chmod 755 media chroma_db
```

### Step 6: Gunicorn Setup

Create systemd service file:

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add:
```ini
[Unit]
Description=Gunicorn daemon for Employee Verification Platform
After=network.target

[Service]
User=employeeverif
Group=www-data
WorkingDirectory=/home/employeeverif/employee_verification_platform
Environment="PATH=/home/employeeverif/employee_verification_platform/venv/bin"
ExecStart=/home/employeeverif/employee_verification_platform/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/home/employeeverif/employee_verification_platform/gunicorn.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

### Step 7: Nginx Setup

```bash
sudo nano /etc/nginx/sites-available/employee_verification
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/employeeverif/employee_verification_platform/staticfiles/;
    }
    
    location /media/ {
        alias /home/employeeverif/employee_verification_platform/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/employeeverif/employee_verification_platform/gunicorn.sock;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/employee_verification /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 8: SSL/HTTPS (Optional but Recommended)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Step 9: Firewall Setup

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### Maintenance Commands

```bash
# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# View logs
sudo journalctl -u gunicorn
sudo tail -f /var/log/nginx/error.log

# Update code
cd /home/employeeverif/employee_verification_platform
git pull  # or upload new files
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

## 📊 API Architecture

### Service Layer

The application uses a clean service layer architecture:

#### FaceService (`employees/services/face_service.py`)

```python
# Extract facial embedding
embedding = FaceService.extract_embedding(image_path)

# Validate image
validation = FaceService.validate_image(image_path)

# Convert formats
embedding_list = FaceService.embedding_to_list(embedding)
```

#### ChromaService (`employees/services/chroma_service.py`)

```python
# Add employee embedding
ChromaService.add_employee_embedding(uuid, embedding, metadata)

# Search for match
result = ChromaService.search_embedding(query_embedding)

# Delete embedding
ChromaService.delete_employee_embedding(uuid)

# Get statistics
stats = ChromaService.get_collection_stats()
```

## 🧪 Testing

### Manual Testing

1. **Add Employee Test**:
   - Upload photo with one face → Success
   - Upload photo with no face → Error
   - Upload photo with multiple faces → Error
   - Upload non-image file → Error

2. **Verify Employee Test**:
   - Upload photo of registered employee → Match found
   - Upload photo of unregistered person → No match
   - Upload different angle of same person → Match found (if similarity ≥ threshold)

### Database Testing

```bash
# Check employee count
python manage.py shell
>>> from employees.models import Employee
>>> Employee.objects.count()

# Check ChromaDB
>>> from employees.services import ChromaService
>>> ChromaService.get_collection_stats()
```

## 🐛 Troubleshooting

### Common Issues

**1. "No face detected" error**
- Ensure photo has good lighting
- Face should be clearly visible
- Try front-facing angle
- Check image quality

**2. ChromaDB errors**
- Ensure `chroma_db` directory exists
- Check write permissions
- Restart application

**3. Import errors for DeepFace**
- Install all requirements: `pip install -r requirements.txt`
- Some models download on first use (may take time)

**4. Media files not displaying**
- Check `MEDIA_ROOT` and `MEDIA_URL` settings
- Ensure media directory exists
- In production, configure Nginx to serve media files

**5. Database connection errors**
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Long random string |
| `DEBUG` | Debug mode | True/False |
| `ALLOWED_HOSTS` | Allowed hostnames | localhost,domain.com |
| `DATABASE_ENGINE` | Database backend | django.db.backends.postgresql |
| `DATABASE_NAME` | Database name | employee_verification |
| `DATABASE_USER` | Database user | dbuser |
| `DATABASE_PASSWORD` | Database password | secure_password |
| `DATABASE_HOST` | Database host | localhost |
| `DATABASE_PORT` | Database port | 5432 |
| `SIMILARITY_THRESHOLD` | Face match threshold | 0.65 |
| `MAX_UPLOAD_SIZE` | Max file size (bytes) | 5242880 |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB storage path | chroma_db |

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [DeepFace GitHub](https://github.com/serengil/deepface)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [ArcFace Paper](https://arxiv.org/abs/1801.07698)

## 🤝 Contributing

This is a production prototype. For improvements:
1. Add tests (pytest, pytest-django)
2. Add API endpoints (Django REST Framework)
3. Implement background tasks (Celery)
4. Add monitoring (Sentry, New Relic)
5. Implement caching (Redis)

## 📄 License

This project is provided as-is for educational and commercial use.

## 👨‍💻 Support

For issues or questions, refer to the troubleshooting section or check the service layer code for implementation details.

---

**Built with Django, DeepFace, and ChromaDB** 🚀
