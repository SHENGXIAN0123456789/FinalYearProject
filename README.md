# Job Market Analysis System

A comprehensive job market analysis system that scrapes job postings from major Malaysian job portals (JobStreet and RiceBowl), processes the data, and provides analytical insights through a web dashboard.

## 📋 Project Overview

This Final Year Project consists of three main components:
- **Web Scraper**: Automated data collection from job portals using Scrapy
- **Data Processing Pipeline**: Cleaning, normalization, and database insertion
- **Web Dashboard**: Flask-based analytics interface for job market insights

## 🎯 Features

- **Automated Job Scraping**: Collect job postings from JobStreet and RiceBowl
- **Data Cleaning & Processing**: Standardize job categories, skills, locations, and types
- **Database Storage**: PostgreSQL database with optimized schema
- **Analytics Dashboard**: Interactive web interface for data visualization
- **Job Market Insights**: Analysis by location, categories, skills, and job types
- **Date Range Filtering**: Historical job market trend analysis

## 🛠️ Prerequisites

Before running this project, ensure you have the following installed:

- **Python 3.11+** - Programming language runtime
- **PostgreSQL 16.8+** - Database server
- **Git** - Version control system
- **pip** - Python package manager

### System Requirements
- Windows/Linux/macOS
- 4GB+ RAM recommended
- 2GB+ free disk space

## 📦 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd FinalYearProject
```

### 2. Database Setup
1. Install and start PostgreSQL server
2. Create a database named `FYP`:
```sql
CREATE DATABASE FYP;
```
3. Update database credentials in `.env` file (create if doesn't exist):
```env
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=FYP
SECRET_KEY=your_secret_key_here
```

### 3. Initialize Database Schema
```bash
cd data/db/init
python init_db.py
```

### 4. Install Dependencies

#### For Web Scraper:
```bash
cd myScraper
pip install -r requirements.txt
```

#### For Data Processing:
```bash
cd data
pip install -r requirements.txt
```

#### For Web Dashboard:
```bash
cd web
pip install -r requirements.txt
```

## 🚀 Usage

### 1. Data Collection (Web Scraping)
```bash
cd myScraper
# Scrape JobStreet
scrapy crawl jobstreet
# Scrape RiceBowl
scrapy crawl ricebowl
```

### 2. Data Processing
```bash
cd data/cleaner
# Clean JobStreet data
python js_cleaner.py
# Clean RiceBowl data
python rb_cleaner.py
```

### 3. Database Insertion
```bash
cd data/db/insert
python insert.py
```

### 4. Run Web Dashboard
```bash
cd web
python run.py
```
Access the dashboard at `http://localhost:5000`

## 📁 Project Structure

```
FinalYearProject/
├── myScraper/              # Scrapy web scraping project
│   ├── myScraper/
│   │   ├── spiders/        # Spider implementations
│   │   ├── items.py        # Data models
│   │   └── settings.py     # Scrapy configuration
│   └── requirements.txt
├── data/                   # Data processing pipeline
│   ├── cleaner/           # Data cleaning scripts
│   ├── db/                # Database operations
│   │   ├── init/          # Database initialization
│   │   └── insert/        # Data insertion scripts
│   └── requirements.txt
├── web/                   # Flask web application
│   ├── templates/         # HTML templates
│   ├── static/           # CSS, JS, images
│   ├── app.py            # Flask application factory
│   ├── routes.py         # API and page routes
│   └── requirements.txt
└── README.md
```

## 🔧 Configuration

### Scraping Configuration
- API keys and proxy settings in `myScraper/myScraper/settings.py`
- Spider-specific settings in individual spider files

### Database Configuration
- Connection settings via environment variables
- Schema initialization scripts in `data/db/init/`

### Web Application Configuration
- Flask settings in `web/app.py`
- Environment variables in `.env` file

## 📊 Data Sources

- **JobStreet Malaysia**: Job postings from major Malaysian job portal
- **RiceBowl**: Technology-focused job postings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📝 License

This project is developed as part of a Final Year Project for academic purposes.

## ⚠️ Disclaimer

This tool is designed for educational and research purposes. Please ensure compliance with the terms of service of the websites being scraped and respect robots.txt files.

## 🆘 Troubleshooting

### Common Issues:
1. **Database Connection Error**: Verify PostgreSQL is running and credentials are correct
2. **Scraping Blocked**: Check proxy settings and rate limiting
3. **Module Import Error**: Ensure all requirements are installed in correct virtual environment

For additional support, please check the issue tracker or contact the development team.