# Revenue Forecast Sync

Revenue Forecast Sync is a Python application that synchronizes MySQL data to the OptiQo Revenue Forecast API via webhook integration. Built for production with Docker containerization and Kubernetes deployment support.

## Features

- ✅ MySQL bi_data database integration with configurable connection
- ✅ OptiQo API webhook integration (`/webhook` endpoint)
- ✅ Docker containerization with multi-stage builds
- ✅ Kubernetes deployment ready with health checks
- ✅ Jenkins CI/CD pipeline for automated Docker builds
- ✅ Full/incremental sync modes with state persistence
- ✅ Batch processing with retry logic and comprehensive error handling
- ✅ Production tested with 798K+ records successfully processed

## Jenkins Build

This project uses Jenkins for automated Docker image builds and deployment.

### Pipeline Configuration

- **Jenkinsfile**: `build.jenkinsfile`
- **Docker Registry**: `docker.io/strakertech/revenue-forecast-sync`
- **Tags**: `prod-latest` and `prod-{git-sha}`

### Jenkins Variables

Configure these variables in your Jenkins job:

```
APPLICATION = "revenue-forecast-sync"
REPO = "strakergroup/revenue-forecast-sync"  
BRANCH = "main"
TAG = "prod"
DOCKER_PASSWORD = "${DOCKER_REGISTRY_PASSWORD}"
```

### Build Process

1. **Git Clone**: Clones the repository using SSH
2. **Container Build**: Uses `buildah` to create Docker images
3. **Registry Push**: Pushes tagged images to Docker registry

## Docker Images

### Production Image

```bash
docker pull strakertech/revenue-forecast-sync:prod-latest
```

### Local Development

```bash
# Build locally
docker build -t revenue-forecast-sync:dev .

# Run with Docker Compose
docker-compose up revenue-forecast-sync
```

## Configuration

### Environment Variables

Create a `.env` file (see `.env.example`):

```env
MYSQL_HOST=your-mysql-host
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password
MYSQL_DATABASE=bi_data
MYSQL_PORT=3306
APP_URL=https://optiqo.straker.co
BOOKINGS_SYNC_API_KEY=your-api-key-here
```

## Kubernetes Deployment

### Prerequisites

1. Create namespace:
```bash
kubectl create namespace revenue-forecast-sync
```

2. Create secret from environment file:
```bash
kubectl create secret generic revenue-forecast-sync-env \
  --from-file=revenue-forecast-sync-env.env=.env \
  --namespace=revenue-forecast-sync
```

### Deploy

```bash
kubectl apply -f k8s-deployment.yaml
```

### Monitor

```bash
kubectl logs -f deployment/revenue-forecast-sync -n revenue-forecast-sync
kubectl get pods -n revenue-forecast-sync
```

## Usage

### Command Line

```bash
# Incremental sync (default)
python sync_app.py

# Full refresh
python sync_app.py --full

# Dry run (no API calls)
python sync_app.py --dry-run
```

### Production Schedule

Configure as Kubernetes CronJob for automated scheduling:

```yaml
schedule: "0 */6 * * *"  # Every 6 hours
```

## API Integration

### Endpoint
- **URL**: `https://optiqo.straker.co/webhook`
- **Method**: POST
- **Authentication**: X-Api-Key header
- **Format**: JSON payload with data array

### Data Schema

```json
{
  "data": [
    {
      "Customer": "Client Name",
      "Group": "Group Name", 
      "Entity": "Entity Name",
      "TJ": "TJ123456",
      "Date": "2026-02-25T10:30:00",
      "TJAmount (in Sales Order currency)": 1500.00,
      "Currency": "USD",
      "Status": "Active",
      "Gross Margin": 0.25
    }
  ]
}
```

## Testing

### Test Suite

```bash
# Configuration test
python test_config.py

# API endpoint test
python test_api_direct.py

# Docker integration test
./test_docker.sh
```

### Production Validation

Successfully tested with:
- **798,039 records** processed
- **3,991 batches** sent 
- **100% success rate** to `/webhook` endpoint
- **~1 hour processing time** for full dataset

## Development

### Local Setup

```bash
# Clone repository
git clone https://github.com/strakergroup/revenue-forecast-sync.git
cd revenue-forecast-sync

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run application
python sync_app.py --dry-run
```

### Project Structure

```
revenue-forecast-sync/
├── sync_app.py              # Main application
├── Dockerfile               # Production container
├── docker-compose.yml       # Local development
├── build.jenkinsfile        # Jenkins CI/CD pipeline
├── k8s-deployment.yaml      # Kubernetes deployment
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── README.md               # This file
└── tests/                  # Test suite
    ├── test_config.py
    ├── test_api_direct.py
    └── test_docker.sh
```

## Monitoring and Logging

### Docker Logs

```bash
docker logs revenue-forecast-sync-production
```

### Kubernetes Logs

```bash
kubectl logs -f deployment/revenue-forecast-sync -n revenue-forecast-sync
```

### Health Checks

- **Docker**: Health check every 5 minutes
- **Kubernetes**: Startup and liveness probes configured
- **Application**: Comprehensive error handling with retries

## Support

For issues or questions:

1. Check application logs for detailed error messages
2. Verify environment configuration matches requirements  
3. Test API connectivity with `test_api_direct.py`
4. Create GitHub issues for bugs or feature requests

## License

Internal Straker Limited project.