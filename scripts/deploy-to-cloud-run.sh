#!/bin/bash

# Cloud Run 배포 스크립트
# 사용법: ./scripts/deploy-to-cloud-run.sh [PROJECT_ID] [REGION]

set -e

# 기본값 설정
PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"asia-northeast3"}
GAR_LOCATION=${3:-"asia-northeast3"}
REPOSITORY="nie-services"

echo "🚀 Deploying NIE services to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "GAR Location: $GAR_LOCATION"

# 현재 프로젝트 설정
gcloud config set project $PROJECT_ID

# Flask App 배포
echo "📦 Deploying Flask WordCloud App..."
gcloud run deploy nie-flask-app \
  --image=$GAR_LOCATION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/flask-app:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --port=5000 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --timeout=300s \
  --set-env-vars="FLASK_ENV=production" \
  --quiet

# MCP HTTP Server 배포
echo "📦 Deploying MCP HTTP Server..."
gcloud run deploy nie-mcp-http \
  --image=$GAR_LOCATION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/mcp-http:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --timeout=300s \
  --quiet

# MCP SQLite Server 배포
echo "📦 Deploying MCP SQLite Server..."
gcloud run deploy nie-mcp-sqlite \
  --image=$GAR_LOCATION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/mcp-sqlite:latest \
  --region=$REGION \
  --platform=managed \
  --no-allow-unauthenticated \
  --port=3000 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=300s \
  --quiet

# Monitoring Service 배포
echo "📦 Deploying Monitoring Service..."
gcloud run deploy nie-monitoring \
  --image=$GAR_LOCATION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/monitoring:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --port=9090 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=300s \
  --quiet

echo ""
echo "✅ Deployment completed!"
echo ""
echo "🌐 Service URLs:"
echo "Flask App: $(gcloud run services describe nie-flask-app --region=$REGION --format='value(status.url)')"
echo "MCP HTTP: $(gcloud run services describe nie-mcp-http --region=$REGION --format='value(status.url)')"
echo "MCP SQLite: $(gcloud run services describe nie-mcp-sqlite --region=$REGION --format='value(status.url)')"
echo "Monitoring: $(gcloud run services describe nie-monitoring --region=$REGION --format='value(status.url)')"
echo ""
echo "📋 To manage services:"
echo "gcloud run services list --region=$REGION"
echo ""
echo "📊 To view logs:"
echo "gcloud logs read --project=$PROJECT_ID --filter='resource.type=cloud_run_revision'"