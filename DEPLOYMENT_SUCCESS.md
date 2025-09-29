# 🚀 NIE 프로젝트 Google Cloud 배포 완료!

## 배포된 서비스들

이제 다음 서비스들이 Google Cloud Run에 자동 배포됩니다:

### 1. Flask WordCloud App
- **포트**: 5000
- **기능**: 워드클라우드 생성 및 시각화
- **리소스**: 1Gi 메모리, 1 CPU

### 2. MCP HTTP Server  
- **포트**: 8080
- **기능**: Model Context Protocol HTTP 서버
- **리소스**: 512Mi 메모리, 1 CPU

### 3. MCP SQLite Server
- **포트**: 3000  
- **기능**: SQLite 데이터베이스 MCP 서버
- **리소스**: 512Mi 메모리, 1 CPU
- **보안**: 인증 필요 (no-allow-unauthenticated)

### 4. Monitoring Service
- **포트**: 9090
- **기능**: 시스템 모니터링 및 알림
- **리소스**: 512Mi 메모리, 1 CPU

## 자동 배포 파이프라인

GitHub의 main 브랜치에 커밋할 때마다 자동으로:

1. 🔨 **Docker 이미지 빌드** - 각 서비스별로 최적화된 컨테이너 이미지 생성
2. 📦 **Google Artifact Registry 푸시** - 안전한 컨테이너 레지스트리에 저장
3. 🌐 **Cloud Run 배포** - 서버리스 환경에 자동 배포
4. ✅ **URL 출력** - 배포된 서비스 URL 확인 가능

## 모니터링 및 관리

- **GitHub Actions**: https://github.com/Suntae-Kim2020/nie/actions
- **Google Cloud Console**: https://console.cloud.google.com/
- **Cloud Run 서비스**: https://console.cloud.google.com/run
- **Artifact Registry**: https://console.cloud.google.com/artifacts

## 배포 완료 날짜

**날짜**: 2025년 9월 29일  
**상태**: ✅ 성공적으로 구성 완료

이제 코드 변경사항을 커밋하면 자동으로 Google Cloud에 배포됩니다! 🎉