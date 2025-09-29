#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
조류 충돌 모니터링 통합 시스템
전체 시스템 구성요소를 통합하여 운영하는 마스터 컨트롤러
"""

import os
import sys
import json
import sqlite3
import subprocess
import threading
import time
import webbrowser
from datetime import datetime, timedelta
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BirdCollisionIntegratedSystem:
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.web_server_process = None
        self.monitoring_thread = None
        self.system_status = {
            "database": False,
            "web_server": False,
            "monitoring": False,
            "notifications": False
        }
        self.setup_system()
    
    def setup_system(self):
        """시스템 초기화"""
        logger.info("조류 충돌 모니터링 통합 시스템 초기화 중...")
        
        # 필요한 파일들 확인
        self.check_system_requirements()
        
        # 데이터베이스 상태 확인
        self.check_database_status()
    
    def check_system_requirements(self):
        """시스템 요구사항 확인"""
        required_files = [
            "조류유리창_충돌사고_2023_2024_전국.gpkg",
            "real_time_monitoring_dashboard.html",
            "integrated_monitoring_system.py",
            "notification_system.py"
        ]
        
        missing_files = []
        for file in required_files:
            if not (self.base_path / file).exists():
                missing_files.append(file)
        
        if missing_files:
            logger.warning(f"누락된 파일: {missing_files}")
        else:
            logger.info("모든 필수 파일이 존재합니다.")
    
    def check_database_status(self):
        """데이터베이스 상태 확인"""
        try:
            db_path = self.base_path / "조류유리창_충돌사고_2023_2024_전국.gpkg"
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM 조류유리창_충돌사고_2023_2024_전국")
                count = cursor.fetchone()[0]
                logger.info(f"데이터베이스 연결 성공: {count}개 레코드")
                self.system_status["database"] = True
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            self.system_status["database"] = False
    
    def start_web_server(self, port=8000):
        """웹 서버 시작"""
        try:
            logger.info(f"웹 서버 시작 중... (포트: {port})")
            self.web_server_process = subprocess.Popen(
                [sys.executable, "-m", "http.server", str(port)],
                cwd=str(self.base_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 서버 시작 대기
            time.sleep(3)
            
            if self.web_server_process.poll() is None:
                logger.info(f"웹 서버 시작 완료: http://localhost:{port}")
                self.system_status["web_server"] = True
                return True
            else:
                logger.error("웹 서버 시작 실패")
                return False
                
        except Exception as e:
            logger.error(f"웹 서버 시작 오류: {e}")
            return False
    
    def stop_web_server(self):
        """웹 서버 종료"""
        if self.web_server_process:
            try:
                self.web_server_process.terminate()
                self.web_server_process.wait(timeout=5)
                logger.info("웹 서버 종료 완료")
                self.system_status["web_server"] = False
            except subprocess.TimeoutExpired:
                self.web_server_process.kill()
                logger.warning("웹 서버 강제 종료")
    
    def start_monitoring_system(self):
        """모니터링 시스템 시작"""
        def monitoring_worker():
            try:
                logger.info("모니터링 시스템 시작...")
                
                # integrated_monitoring_system.py 실행
                monitoring_script = self.base_path / "integrated_monitoring_system.py"
                if monitoring_script.exists():
                    # 모니터링 스크립트를 모듈로 가져와서 실행
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("monitoring", monitoring_script)
                    monitoring_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(monitoring_module)
                    
                    # 모니터링 시스템 인스턴스 생성 및 실행
                    monitor = monitoring_module.BirdCollisionMonitoringSystem()
                    
                    while self.system_status.get("monitoring", False):
                        try:
                            report = monitor.create_monitoring_report()
                            if report:
                                logger.info(f"모니터링 보고서 생성: {len(report.get('active_alerts', []))}개 알림")
                            time.sleep(300)  # 5분마다 실행
                        except Exception as e:
                            logger.error(f"모니터링 중 오류: {e}")
                            time.sleep(60)
                else:
                    logger.error("모니터링 스크립트를 찾을 수 없습니다.")
                    
            except Exception as e:
                logger.error(f"모니터링 시스템 오류: {e}")
                self.system_status["monitoring"] = False
        
        try:
            self.monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
            self.monitoring_thread.start()
            self.system_status["monitoring"] = True
            logger.info("모니터링 시스템 백그라운드 실행 시작")
            return True
        except Exception as e:
            logger.error(f"모니터링 시스템 시작 실패: {e}")
            return False
    
    def stop_monitoring_system(self):
        """모니터링 시스템 종료"""
        self.system_status["monitoring"] = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.info("모니터링 시스템 종료 중...")
            # 스레드가 자연스럽게 종료되기를 기다림
    
    def setup_notification_system(self):
        """알림 시스템 설정"""
        try:
            notification_script = self.base_path / "notification_system.py"
            if notification_script.exists():
                logger.info("알림 시스템 설정 완료")
                self.system_status["notifications"] = True
                return True
            else:
                logger.warning("알림 시스템 스크립트를 찾을 수 없습니다.")
                return False
        except Exception as e:
            logger.error(f"알림 시스템 설정 실패: {e}")
            return False
    
    def open_dashboard(self, port=8000):
        """대시보드 웹 페이지 열기"""
        try:
            dashboard_url = f"http://localhost:{port}/real_time_monitoring_dashboard.html"
            logger.info(f"대시보드 열기: {dashboard_url}")
            webbrowser.open(dashboard_url)
            return True
        except Exception as e:
            logger.error(f"대시보드 열기 실패: {e}")
            return False
    
    def generate_system_report(self):
        """시스템 상태 보고서 생성"""
        report = {
            "system_status": self.system_status,
            "timestamp": datetime.now().isoformat(),
            "uptime": self.get_system_uptime(),
            "components": {
                "database": {
                    "status": self.system_status["database"],
                    "description": "조류 충돌 데이터베이스 연결 상태"
                },
                "web_server": {
                    "status": self.system_status["web_server"],
                    "description": "웹 서버 실행 상태"
                },
                "monitoring": {
                    "status": self.system_status["monitoring"],
                    "description": "실시간 모니터링 시스템 상태"
                },
                "notifications": {
                    "status": self.system_status["notifications"],
                    "description": "알림 시스템 설정 상태"
                }
            },
            "urls": {
                "dashboard": "http://localhost:8000/real_time_monitoring_dashboard.html",
                "policy_viewer": "http://localhost:8000/policy_recommendations.html",
                "data_explorer": "http://localhost:8000/bird_collision_dashboard.html",
                "map_viewer": "http://localhost:8000/bird_collision_map.html"
            }
        }
        
        # 보고서 파일로 저장
        report_file = self.base_path / "system_status_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
    
    def get_system_uptime(self):
        """시스템 가동 시간 계산"""
        # 간단한 가동시간 시뮬레이션
        return "시스템 가동 중"
    
    def run_health_check(self):
        """시스템 헬스체크"""
        logger.info("시스템 헬스체크 실행 중...")
        
        health_status = {
            "overall": "healthy",
            "checks": {}
        }
        
        # 데이터베이스 확인
        self.check_database_status()
        health_status["checks"]["database"] = self.system_status["database"]
        
        # 웹 서버 확인
        if self.web_server_process and self.web_server_process.poll() is None:
            health_status["checks"]["web_server"] = True
        else:
            health_status["checks"]["web_server"] = False
            self.system_status["web_server"] = False
        
        # 모니터링 시스템 확인
        health_status["checks"]["monitoring"] = self.system_status["monitoring"]
        
        # 전체 상태 결정
        if not all(health_status["checks"].values()):
            health_status["overall"] = "degraded"
        
        logger.info(f"헬스체크 완료: {health_status['overall']}")
        return health_status
    
    def start_full_system(self, port=8000, open_browser=True):
        """전체 시스템 시작"""
        logger.info("=" * 60)
        logger.info("🐦 조류 충돌 모니터링 통합 시스템 시작")
        logger.info("=" * 60)
        
        # 1. 웹 서버 시작
        if self.start_web_server(port):
            logger.info("✅ 웹 서버 시작 완료")
        else:
            logger.error("❌ 웹 서버 시작 실패")
            return False
        
        # 2. 모니터링 시스템 시작
        if self.start_monitoring_system():
            logger.info("✅ 모니터링 시스템 시작 완료")
        else:
            logger.warning("⚠️ 모니터링 시스템 시작 실패")
        
        # 3. 알림 시스템 설정
        if self.setup_notification_system():
            logger.info("✅ 알림 시스템 설정 완료")
        else:
            logger.warning("⚠️ 알림 시스템 설정 실패")
        
        # 4. 시스템 보고서 생성
        report = self.generate_system_report()
        logger.info("✅ 시스템 상태 보고서 생성 완료")
        
        # 5. 브라우저에서 대시보드 열기
        if open_browser:
            time.sleep(2)  # 서버 안정화 대기
            self.open_dashboard(port)
        
        logger.info("=" * 60)
        logger.info("🎯 시스템 시작 완료!")
        logger.info(f"📊 대시보드: http://localhost:{port}/real_time_monitoring_dashboard.html")
        logger.info(f"📋 정책 문서: http://localhost:{port}/policy_recommendations.html")
        logger.info(f"🗺️ 지도 뷰어: http://localhost:{port}/bird_collision_map.html")
        logger.info(f"📈 데이터 탐색기: http://localhost:{port}/bird_collision_dashboard.html")
        logger.info("=" * 60)
        
        return True
    
    def stop_full_system(self):
        """전체 시스템 종료"""
        logger.info("시스템 종료 중...")
        
        self.stop_monitoring_system()
        self.stop_web_server()
        
        # 시스템 상태 초기화
        self.system_status = {
            "database": False,
            "web_server": False,
            "monitoring": False,
            "notifications": False
        }
        
        logger.info("시스템 종료 완료")
    
    def interactive_menu(self):
        """인터랙티브 메뉴"""
        while True:
            print("\n🐦 조류 충돌 모니터링 시스템 관리")
            print("=" * 40)
            print("1. 전체 시스템 시작")
            print("2. 시스템 상태 확인")
            print("3. 헬스체크 실행")
            print("4. 대시보드 열기")
            print("5. 시스템 종료")
            print("6. 종료")
            print("=" * 40)
            
            choice = input("선택하세요 (1-6): ").strip()
            
            if choice == "1":
                self.start_full_system()
            elif choice == "2":
                report = self.generate_system_report()
                print("\n📊 시스템 상태:")
                for component, status in report["system_status"].items():
                    print(f"  • {component}: {'✅ 정상' if status else '❌ 오류'}")
            elif choice == "3":
                health = self.run_health_check()
                print(f"\n🏥 헬스체크 결과: {health['overall']}")
            elif choice == "4":
                self.open_dashboard()
            elif choice == "5":
                self.stop_full_system()
            elif choice == "6":
                self.stop_full_system()
                print("시스템을 종료합니다.")
                break
            else:
                print("잘못된 선택입니다.")

def main():
    """메인 함수"""
    system = BirdCollisionIntegratedSystem()
    
    # 명령행 인수 확인
    if len(sys.argv) > 1:
        if sys.argv[1] == "--start":
            system.start_full_system()
            try:
                while True:
                    time.sleep(60)
                    system.run_health_check()
            except KeyboardInterrupt:
                system.stop_full_system()
        elif sys.argv[1] == "--status":
            report = system.generate_system_report()
            print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        # 인터랙티브 모드
        system.interactive_menu()

if __name__ == "__main__":
    main()