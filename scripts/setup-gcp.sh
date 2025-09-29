#!/bin/bash

# Google Cloud Project Setup Script for NIE Services
# This script sets up the necessary GCP resources for deploying NIE services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-your-project-id}"
REGION="${REGION:-asia-northeast3}"
REPOSITORY_NAME="${REPOSITORY_NAME:-nie-services}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-nie-github-actions}"

echo -e "${GREEN}🚀 Setting up Google Cloud Platform for NIE Services${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Repository: $REPOSITORY_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️ You are not logged in to gcloud. Please run 'gcloud auth login'${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}📋 Setting project to $PROJECT_ID...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    iam.googleapis.com \
    cloudresourcemanager.googleapis.com

# Create Artifact Registry repository
echo -e "${YELLOW}📦 Creating Artifact Registry repository...${NC}"
if ! gcloud artifacts repositories describe $REPOSITORY_NAME --location=$REGION >/dev/null 2>&1; then
    gcloud artifacts repositories create $REPOSITORY_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="NIE Services Container Repository"
    echo -e "${GREEN}✅ Repository created successfully${NC}"
else
    echo -e "${GREEN}✅ Repository already exists${NC}"
fi

# Create service account for GitHub Actions
echo -e "${YELLOW}👤 Creating service account for GitHub Actions...${NC}"
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" >/dev/null 2>&1; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="GitHub Actions Service Account for NIE" \
        --description="Service account for GitHub Actions to deploy NIE services"
    echo -e "${GREEN}✅ Service account created${NC}"
else
    echo -e "${GREEN}✅ Service account already exists${NC}"
fi

# Grant necessary permissions
echo -e "${YELLOW}🔐 Granting permissions to service account...${NC}"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Required roles for the service account
ROLES=(
    "roles/artifactregistry.writer"
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/cloudbuild.builds.builder"
)

for role in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role"
    echo -e "${GREEN}✅ Granted $role${NC}"
done

# Setup Workload Identity Federation for GitHub Actions
echo -e "${YELLOW}🔗 Setting up Workload Identity Federation...${NC}"

# Create workload identity pool
WIF_POOL_ID="github-pool"
if ! gcloud iam workload-identity-pools describe $WIF_POOL_ID --location="global" >/dev/null 2>&1; then
    gcloud iam workload-identity-pools create $WIF_POOL_ID \
        --location="global" \
        --display-name="GitHub Actions Pool"
    echo -e "${GREEN}✅ Workload Identity Pool created${NC}"
else
    echo -e "${GREEN}✅ Workload Identity Pool already exists${NC}"
fi

# Create workload identity provider
WIF_PROVIDER_ID="github-provider"
REPO_NAME="${GITHUB_REPO:-your-username/nie}"  # Update this

if ! gcloud iam workload-identity-pools providers describe $WIF_PROVIDER_ID \
    --workload-identity-pool=$WIF_POOL_ID --location="global" >/dev/null 2>&1; then
    
    gcloud iam workload-identity-pools providers create-oidc $WIF_PROVIDER_ID \
        --workload-identity-pool=$WIF_POOL_ID \
        --location="global" \
        --issuer-uri="https://token.actions.githubusercontent.com" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --attribute-condition="assertion.repository=='$REPO_NAME'"
    echo -e "${GREEN}✅ Workload Identity Provider created${NC}"
else
    echo -e "${GREEN}✅ Workload Identity Provider already exists${NC}"
fi

# Bind service account to workload identity
echo -e "${YELLOW}🔗 Binding service account to workload identity...${NC}"
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/$(gcloud config get-value project --quiet)/locations/global/workloadIdentityPools/$WIF_POOL_ID/attribute.repository/$REPO_NAME"

# Output configuration information
echo -e "${GREEN}"
echo "=============================================="
echo "🎉 Setup completed successfully!"
echo "=============================================="
echo -e "${NC}"

echo "Add these secrets to your GitHub repository:"
echo ""
echo "GCP_PROJECT_ID: $PROJECT_ID"
echo "WIF_PROVIDER: projects/$(gcloud config get-value project --quiet)/locations/global/workloadIdentityPools/$WIF_POOL_ID/providers/$WIF_PROVIDER_ID"
echo "WIF_SERVICE_ACCOUNT: $SERVICE_ACCOUNT_EMAIL"
echo ""

echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Add the above secrets to your GitHub repository settings"
echo "2. Update the GITHUB_REPO variable in this script with your actual repository"
echo "3. Push your code to trigger the GitHub Actions workflow"
echo "4. Monitor the deployment in GitHub Actions and Cloud Console"
echo ""

echo -e "${GREEN}🔧 Useful commands:${NC}"
echo "View Artifact Registry: gcloud artifacts repositories list"
echo "View Cloud Run services: gcloud run services list"
echo "View service account: gcloud iam service-accounts list"