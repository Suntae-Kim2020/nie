#!/bin/bash

# Local Deployment Test Script for NIE Services
# This script builds and runs all services locally using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Local Deployment of NIE Services${NC}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    echo -e "${RED}❌ docker-compose is not installed. Please install it first.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p data logs

# Stop any existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.services.yml down --remove-orphans

# Build and start services
echo -e "${YELLOW}🔨 Building and starting services...${NC}"
docker-compose -f docker-compose.services.yml up --build -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Health check
echo -e "${YELLOW}🏥 Performing health checks...${NC}"

# Check Flask App
if curl -f http://localhost:5000/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Flask App is running${NC}"
else
    echo -e "${RED}❌ Flask App is not responding${NC}"
fi

# Check MCP HTTP Server
if curl -f http://localhost:8081/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ MCP HTTP Server is running${NC}"
else
    echo -e "${RED}❌ MCP HTTP Server is not responding${NC}"
fi

# Check File Server
if curl -f http://localhost:8000/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ File Server is running${NC}"
else
    echo -e "${RED}❌ File Server is not responding${NC}"
fi

# Show running containers
echo -e "${YELLOW}📋 Running containers:${NC}"
docker-compose -f docker-compose.services.yml ps

# Show service URLs
echo -e "${GREEN}"
echo "=============================================="
echo "🎉 Local deployment completed!"
echo "=============================================="
echo -e "${NC}"

echo "Service URLs:"
echo "- Flask WordCloud App: http://localhost:5000"
echo "- MCP HTTP Server: http://localhost:8081"
echo "- File Server: http://localhost:8000"
echo "- Monitoring (if configured): http://localhost:9090"
echo ""

echo -e "${YELLOW}📝 Useful commands:${NC}"
echo "View logs: docker-compose -f docker-compose.services.yml logs -f [service-name]"
echo "Stop services: docker-compose -f docker-compose.services.yml down"
echo "Restart services: docker-compose -f docker-compose.services.yml restart"
echo "View service status: docker-compose -f docker-compose.services.yml ps"
echo ""

echo -e "${GREEN}🔧 Development mode:${NC}"
echo "To run in development mode with live reload:"
echo "docker-compose -f docker-compose.services.yml -f docker-compose.dev.yml up --build"