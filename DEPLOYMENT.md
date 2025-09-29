# NIE Services - Deployment Guide

🚀 Google Artifact Registry를 통한 클라우드 배포 가이드

## 📋 목차

- [개요](#개요)
- [서비스 아키텍처](#서비스-아키텍처)
- [사전 요구사항](#사전-요구사항)
- [로컬 개발 환경 설정](#로컬-개발-환경-설정)
- [Google Cloud 설정](#google-cloud-설정)
- [GitHub Actions 설정](#github-actions-설정)
- [배포 프로세스](#배포-프로세스)
- [모니터링 및 관리](#모니터링-및-관리)
- [문제 해결](#문제-해결)

## 개요

이 프로젝트는 여러 마이크로서비스로 구성된 NIE(News In Education) 플랫폼입니다:

- **Flask WordCloud Service**: 워드클라우드 생성 웹 애플리케이션
- **MCP HTTP Server**: Model Context Protocol HTTP 서버
- **MCP SQLite Server**: SQLite 데이터베이스 MCP 서버
- **Monitoring Service**: 통합 모니터링 시스템
- **File Server**: 정적 파일 서빙

## 서비스 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │    │  MCP HTTP       │    │  File Server    │
│   Port: 5000    │    │  Port: 8080     │    │  Port: 8000     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         └───────────────────┬────────────────────────────┘
                            │
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │   (Cloud Run)   │
                    └─────────────────┘
                            │
                    ┌─────────────────┐
                    │ Artifact Registry│
                    │  (GAR Storage)  │
                    └─────────────────┘
```

## 사전 요구사항

### 필수 도구
- [Docker](https://www.docker.com/) (20.10+)
- [Docker Compose](https://docs.docker.com/compose/) (v2.0+)
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
- [Git](https://git-scm.com/)

### Google Cloud Platform
- GCP 프로젝트 (Billing 활성화)
- 다음 API 활성화:
  - Artifact Registry API
  - Cloud Run API
  - Cloud Build API
  - IAM API

## 로컬 개발 환경 설정

### 1. 저장소 클론

```bash
git clone <your-repository-url>
cd nie
```

### 2. 환경 설정

```bash
# Python 가상환경 설정
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 로컬 서비스 실행

```bash
# 모든 서비스를 Docker로 실행
./scripts/local-deploy.sh

# 또는 개별 서비스 실행
python flask_wordcloud.py
python mcp_http_server.py
python mcp_sqlite_server.py
```

### 4. 서비스 접속 확인

- Flask App: http://localhost:5000
- MCP HTTP: http://localhost:8080
- File Server: http://localhost:8000

## Google Cloud 설정

### 1. GCP 프로젝트 설정

```bash
# 프로젝트 ID 설정
export PROJECT_ID="your-project-id"

# 프로젝트 선택
gcloud config set project $PROJECT_ID

# 필요한 API 활성화
gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com
```

### 2. 자동 설정 스크립트 실행

```bash
# 환경변수 설정
export PROJECT_ID="your-project-id"
export GITHUB_REPO="your-username/nie"

# 설정 스크립트 실행
./scripts/setup-gcp.sh
```

### 3. 수동 설정 (선택사항)

<details>
<summary>수동 설정 단계 보기</summary>

#### Artifact Registry 저장소 생성

```bash
gcloud artifacts repositories create nie-services \
    --repository-format=docker \
    --location=asia-northeast3 \
    --description="NIE Services Repository"
```

#### 서비스 계정 생성

```bash
gcloud iam service-accounts create nie-github-actions \
    --display-name="GitHub Actions Service Account"
```

#### 권한 부여

```bash
SERVICE_ACCOUNT_EMAIL="nie-github-actions@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.admin"
```

</details>

## GitHub Actions 설정

### 1. GitHub Repository Secrets 설정

Repository Settings > Secrets and variables > Actions에서 다음 secrets 추가:

```
GCP_PROJECT_ID: your-project-id
WIF_PROVIDER: projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
WIF_SERVICE_ACCOUNT: nie-github-actions@your-project-id.iam.gserviceaccount.com
```

### 2. Workload Identity Federation 설정

setup-gcp.sh 스크립트 실행 후 출력되는 정보를 GitHub Secrets에 추가하세요.

## 배포 프로세스

### 자동 배포 (권장)

1. **코드 푸시**
   ```bash
   git add .
   git commit -m "Deploy to GAR"
   git push origin main
   ```

2. **GitHub Actions 모니터링**
   - GitHub Repository > Actions 탭에서 워크플로우 진행상황 확인
   - 빌드 완료 후 Cloud Run URL 확인

### 수동 배포

<details>
<summary>수동 배포 단계 보기</summary>

```bash
# 1. Docker 이미지 빌드
docker build -f Dockerfile.flask -t flask-app .
docker build -f Dockerfile.mcp-http -t mcp-http .

# 2. GAR에 태그 지정
docker tag flask-app asia-northeast3-docker.pkg.dev/$PROJECT_ID/nie-services/flask-app:latest
docker tag mcp-http asia-northeast3-docker.pkg.dev/$PROJECT_ID/nie-services/mcp-http:latest

# 3. 인증 설정
gcloud auth configure-docker asia-northeast3-docker.pkg.dev

# 4. 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/$PROJECT_ID/nie-services/flask-app:latest
docker push asia-northeast3-docker.pkg.dev/$PROJECT_ID/nie-services/mcp-http:latest

# 5. Cloud Run 배포
gcloud run deploy nie-flask-app \
    --image=asia-northeast3-docker.pkg.dev/$PROJECT_ID/nie-services/flask-app:latest \
    --region=asia-northeast3 \
    --allow-unauthenticated
```

</details>

## 배포된 서비스 URL

GitHub Actions 완료 후 다음 명령어로 URL 확인:

```bash
# 모든 Cloud Run 서비스 URL 확인
gcloud run services list --format="table(metadata.name,status.url)"

# 개별 서비스 URL 확인
gcloud run services describe nie-flask-app --region=asia-northeast3 --format="value(status.url)"
```

## 모니터링 및 관리

### 로그 확인

```bash
# Cloud Run 로그
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=nie-flask-app" --limit=50

# Artifact Registry 이미지 목록
gcloud artifacts docker images list asia-northeast3-docker.pkg.dev/$PROJECT_ID/nie-services
```

### 리소스 사용량 모니터링

- [Cloud Console - Cloud Run](https://console.cloud.google.com/run)
- [Cloud Console - Artifact Registry](https://console.cloud.google.com/artifacts)
- [Cloud Console - Monitoring](https://console.cloud.google.com/monitoring)

## 문제 해결

### 일반적인 문제

#### 1. Docker 빌드 실패
```bash
# Docker 캐시 클리어
docker system prune -a

# 다시 빌드
docker-compose -f docker-compose.services.yml build --no-cache
```

#### 2. GAR 인증 실패
```bash
# 인증 재설정
gcloud auth configure-docker asia-northeast3-docker.pkg.dev

# 권한 확인
gcloud auth list
```

#### 3. Cloud Run 배포 실패
```bash
# 서비스 삭제 후 재생성
gcloud run services delete nie-flask-app --region=asia-northeast3
```

#### 4. GitHub Actions 실패
- Repository Secrets 확인
- Workload Identity Federation 설정 확인
- 서비스 계정 권한 확인

### 유용한 명령어

```bash
# 전체 리소스 정리
gcloud run services delete --all --region=asia-northeast3
gcloud artifacts repositories delete nie-services --location=asia-northeast3

# 비용 확인
gcloud billing projects describe $PROJECT_ID

# 로그 실시간 모니터링
gcloud logs tail "resource.type=cloud_run_revision"
```

## 추가 리소스

- [Cloud Run 문서](https://cloud.google.com/run/docs)
- [Artifact Registry 문서](https://cloud.google.com/artifact-registry/docs)
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [Docker 문서](https://docs.docker.com/)

---

💡 **문의사항이나 문제가 있으시면 GitHub Issues를 통해 알려주세요!**