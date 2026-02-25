# Revenue Forecast Sync

Python application that syncs revenue forecast data from MySQL bi_data database to the Revenue Forecast API at https://optiqo.straker.co.

## Configuration

Configuration is now managed through `.env` files for better security and portability:

### Local Development

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual configuration:
   ```env
   # MySQL Database Configuration
   MYSQL_HOST=your-mysql-host
   MYSQL_USER=your_db_user
   MYSQL_PASSWORD=your_db_password
   MYSQL_DATABASE=bi_data
   MYSQL_PORT=3306

   # API Configuration
   APP_URL=https://optiqo.straker.co
   BOOKINGS_SYNC_API_KEY=your-api-key-here
   ```

3. Run the application:
   ```bash
   python sync_app.py
   ```

### Kubernetes Deployment

Configuration is managed through Kubernetes secrets:

```bash
# Create namespace
kubectl create namespace job-revenue-forecast-sync

# Create secret from .env file
kubectl create secret generic job-revenue-forecast-sync-env \
  --from-file=.env=secrets/.env \
  --namespace=job-revenue-forecast-sync

# Deploy CronJob
kubectl apply -f job-revenue-forecast-sync.yaml
```

## Security Features

- ✅ **Environment Variables**: Sensitive data in `.env` files
- ✅ **Git Ignored**: `.env` files excluded from version control  
- ✅ **Kubernetes Secrets**: Encrypted storage in cluster
- ✅ **No Hardcoded Secrets**: Credentials not in source code
- ✅ **Fallback Values**: Safe defaults for development

## File Structure

```
revenue-forecast-sync/
├── sync_app.py          # Main application
├── .env                 # Local environment variables (ignored by git)
├── .env.example         # Template for environment variables
├── .gitignore           # Excludes sensitive files
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container configuration
└── README.md           # This file
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MYSQL_HOST` | MySQL server hostname | `reporting-dbproxy-read.straker.io` |
| `MYSQL_USER` | MySQL username | `domo` |
| `MYSQL_PASSWORD` | MySQL password | `your-secure-password` |
| `MYSQL_DATABASE` | Database name | `bi_data` |
| `MYSQL_PORT` | MySQL port | `3306` |
| `APP_URL` | OptiQo application URL | `https://optiqo.straker.co` |
| `BOOKINGS_SYNC_API_KEY` | API authentication key | `8f2b3e91-...` |