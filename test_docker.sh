#!/bin/bash

echo "=== Revenue Forecast Sync - Docker Test ==="

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t revenue-forecast-sync:test .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Test with dry run
echo ""
echo "🧪 Running dry run test in Docker..."
docker run --rm \
    -v $(pwd)/.env:/app/.env:ro \
    revenue-forecast-sync:test \
    python sync_app.py --dry-run

echo ""
echo "📋 Docker test completed"
echo "Next steps:"
echo "- For real database test: ensure MySQL connectivity"  
echo "- For Kubernetes deployment: push image to registry"
echo "- For production: deploy cronjob manifest"