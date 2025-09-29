# Google Cloud 배포 설정 가이드

## 필수 사전 단계

### 1. Google Cloud 프로젝트 생성 또는 선택
1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 기존 프로젝트를 사용하거나 새 프로젝트 생성
3. 프로젝트 ID를 기록해주세요 (예: `nie-project-12345`)

### 2. 필요한 API 활성화
Google Cloud Console에서 다음 API들을 활성화해주세요:
- Artifact Registry API
- Cloud Run API  
- Cloud Build API
- IAM Service Account Credentials API

### 3. Artifact Registry 저장소 생성
```bash
# 명령어 예시 (Google Cloud Shell에서 실행)
gcloud artifacts repositories create nie-repo \
    --repository-format=docker \
    --location=asia-northeast3 \
    --description="NIE project container registry"
```

### 4. Workload Identity Federation 설정

#### 4.1 Workload Identity Pool 생성
```bash
gcloud iam workload-identity-pools create "github-pool" \
    --project="YOUR_PROJECT_ID" \
    --location="global" \
    --display-name="GitHub Actions Pool"
```

#### 4.2 Workload Identity Provider 생성
```bash
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
    --project="YOUR_PROJECT_ID" \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --display-name="GitHub Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"
```

#### 4.3 Service Account 생성
```bash
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions Service Account"
```

#### 4.4 Service Account에 권한 부여
```bash
# Artifact Registry 푸시 권한
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"

# Cloud Run 배포 권한
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

# Service Account 사용자 권한
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

#### 4.5 Workload Identity 바인딩
```bash
gcloud iam service-accounts add-iam-policy-binding \
    --role roles/iam.workloadIdentityUser \
    --member "principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/Suntae-Kim2020/nie" \
    github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 5. GitHub Secrets 설정

GitHub 저장소의 Settings > Secrets and variables > Actions에서 다음 값들을 설정해주세요:

- `GCP_PROJECT_ID`: Google Cloud 프로젝트 ID
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider`
- `GCP_SERVICE_ACCOUNT`: `github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com`
- `GCP_REGION`: `asia-northeast3` (또는 원하는 지역)
- `GAR_LOCATION`: `asia-northeast3` (Artifact Registry 위치)

## 참고사항

- `YOUR_PROJECT_ID`를 실제 Google Cloud 프로젝트 ID로 변경해주세요
- `PROJECT_NUMBER`는 Google Cloud Console에서 확인할 수 있습니다
- 모든 명령어는 적절한 권한을 가진 계정으로 실행해야 합니다

## 다음 단계

설정이 완료되면 GitHub Actions 워크플로우가 자동으로 실행되어 다음을 수행합니다:
1. Docker 이미지 빌드
2. Google Artifact Registry에 푸시
3. Cloud Run에 배포

설정 완료 후 GitHub에서 새로운 커밋을 푸시하면 자동 배포가 시작됩니다.