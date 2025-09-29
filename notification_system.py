#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
조류 충돌 모니터링 알림 시스템
이메일, SMS, 웹훅을 통한 실시간 알림 발송
"""

import smtplib
import json
import requests
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
import os
from dataclasses import dataclass

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class NotificationConfig:
    """알림 설정 데이터 클래스"""
    email_enabled: bool = True
    sms_enabled: bool = False
    webhook_enabled: bool = True
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    webhook_url: str = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    alert_recipients: List[str] = None
    
    def __post_init__(self):
        if self.alert_recipients is None:
            self.alert_recipients = []

class BirdCollisionNotificationSystem:
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.last_alert_time = {}
        self.setup_notification_system()
    
    def setup_notification_system(self):
        """알림 시스템 초기화"""
        logger.info("조류 충돌 알림 시스템 초기화 중...")
        
        # 설정 파일에서 환경변수 로드
        self.load_config_from_env()
    
    def load_config_from_env(self):
        """환경변수에서 설정 로드"""
        self.config.email_username = os.getenv('EMAIL_USERNAME', '')
        self.config.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.config.webhook_url = os.getenv('WEBHOOK_URL', self.config.webhook_url)
        
        # 수신자 목록 로드
        recipients_env = os.getenv('ALERT_RECIPIENTS', '')
        if recipients_env:
            self.config.alert_recipients = recipients_env.split(',')
    
    def should_send_alert(self, alert_key: str, cooldown_minutes: int = 30) -> bool:
        """중복 알림 방지를 위한 쿨다운 체크"""
        current_time = datetime.now()
        
        if alert_key in self.last_alert_time:
            time_diff = current_time - self.last_alert_time[alert_key]
            if time_diff.total_seconds() < cooldown_minutes * 60:
                return False
        
        self.last_alert_time[alert_key] = current_time
        return True
    
    def create_email_content(self, alert_data: Dict) -> tuple:
        """이메일 콘텐츠 생성"""
        subject = f"🚨 조류 충돌 {alert_data['risk_level'].upper()} 알림 - {alert_data['region']}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #dc2626; color: white; padding: 20px; border-radius: 8px; }}
                .content {{ padding: 20px; background: #f9fafb; border-radius: 8px; margin: 10px 0; }}
                .alert-box {{ border-left: 4px solid #dc2626; padding: 15px; background: white; }}
                .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0; }}
                .info-item {{ background: white; padding: 15px; border-radius: 6px; }}
                .actions {{ background: #fffbeb; padding: 15px; border-radius: 6px; border: 1px solid #fbbf24; }}
                .footer {{ text-align: center; color: #6b7280; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🐦 조류 충돌 모니터링 시스템</h1>
                <h2>{alert_data['risk_level'].upper()} 등급 알림</h2>
            </div>
            
            <div class="content">
                <div class="alert-box">
                    <h3>📍 {alert_data['message']}</h3>
                    <p><strong>발생 시간:</strong> {alert_data.get('timestamp', 'N/A')}</p>
                </div>
                
                <div class="info-grid">
                    <div class="info-item">
                        <h4>📊 사고 정보</h4>
                        <p><strong>지역:</strong> {alert_data['region']}</p>
                        <p><strong>사고 건수:</strong> {alert_data['accidents']}건</p>
                        <p><strong>개체 수:</strong> {alert_data['individuals']}마리</p>
                        <p><strong>날짜:</strong> {alert_data['date']}</p>
                    </div>
                    
                    <div class="info-item">
                        <h4>⚠️ 위험도 평가</h4>
                        <p><strong>위험 등급:</strong> {alert_data['risk_level']}</p>
                        <p><strong>대응 우선순위:</strong> {'즉시' if alert_data['risk_level'] == 'critical' else '24시간 내'}</p>
                    </div>
                </div>
                
                <div class="actions">
                    <h4>🎯 권장 조치사항</h4>
                    <ul>
        """
        
        # 권장 조치사항 추가
        for action in alert_data.get('recommended_actions', []):
            html_content += f"<li>{action}</li>"
        
        html_content += """
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>이 알림은 조류 충돌 모니터링 시스템에서 자동으로 생성되었습니다.</p>
                <p>실시간 대시보드: <a href="http://localhost:8000/real_time_monitoring_dashboard.html">모니터링 대시보드</a></p>
            </div>
        </body>
        </html>
        """
        
        return subject, html_content
    
    def send_email_alert(self, alert_data: Dict) -> bool:
        """이메일 알림 발송"""
        if not self.config.email_enabled or not self.config.email_username:
            logger.info("이메일 설정이 없어 이메일 알림을 건너뜁니다.")
            return False
        
        try:
            subject, html_content = self.create_email_content(alert_data)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.email_username
            msg['To'] = ', '.join(self.config.alert_recipients)
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(msg)
            
            logger.info(f"이메일 알림 발송 완료: {alert_data['region']}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 발송 실패: {e}")
            return False
    
    def send_webhook_alert(self, alert_data: Dict) -> bool:
        """웹훅 알림 발송 (Slack, Discord 등)"""
        if not self.config.webhook_enabled:
            logger.info("웹훅이 비활성화되어 알림을 건너뜁니다.")
            return False
        
        try:
            # Slack 형식의 메시지 생성
            webhook_data = {
                "text": f"🚨 조류 충돌 {alert_data['risk_level'].upper()} 알림",
                "attachments": [
                    {
                        "color": "danger" if alert_data['risk_level'] == 'critical' else "warning",
                        "fields": [
                            {
                                "title": "지역",
                                "value": alert_data['region'],
                                "short": True
                            },
                            {
                                "title": "사고 건수",
                                "value": f"{alert_data['accidents']}건",
                                "short": True
                            },
                            {
                                "title": "개체 수",
                                "value": f"{alert_data['individuals']}마리",
                                "short": True
                            },
                            {
                                "title": "위험 등급",
                                "value": alert_data['risk_level'].upper(),
                                "short": True
                            }
                        ],
                        "footer": "조류 충돌 모니터링 시스템",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.config.webhook_url,
                json=webhook_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"웹훅 알림 발송 완료: {alert_data['region']}")
                return True
            else:
                logger.error(f"웹훅 발송 실패: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"웹훅 발송 실패: {e}")
            return False
    
    def send_custom_notification(self, alert_data: Dict, notification_type: str) -> bool:
        """사용자 정의 알림 발송"""
        try:
            # 로컬 알림 파일 생성
            notification_file = f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
            
            if os.path.exists(notification_file):
                with open(notification_file, 'r', encoding='utf-8') as f:
                    alerts = json.load(f)
            else:
                alerts = []
            
            alert_record = {
                "timestamp": datetime.now().isoformat(),
                "type": notification_type,
                "data": alert_data,
                "status": "sent"
            }
            
            alerts.append(alert_record)
            
            with open(notification_file, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, ensure_ascii=False, indent=2)
            
            logger.info(f"사용자 정의 알림 저장 완료: {notification_file}")
            return True
            
        except Exception as e:
            logger.error(f"사용자 정의 알림 저장 실패: {e}")
            return False
    
    def process_alert(self, alert_data: Dict) -> Dict:
        """알림 처리 및 발송"""
        alert_key = f"{alert_data['region']}_{alert_data['date']}_{alert_data['risk_level']}"
        
        # 중복 알림 체크
        if not self.should_send_alert(alert_key):
            logger.info(f"쿨다운 중이므로 알림을 건너뜁니다: {alert_key}")
            return {"status": "skipped", "reason": "cooldown"}
        
        results = {
            "alert_key": alert_key,
            "timestamp": datetime.now().isoformat(),
            "email_sent": False,
            "webhook_sent": False,
            "custom_sent": False
        }
        
        # 이메일 알림 발송
        if self.config.email_enabled and self.config.alert_recipients:
            results["email_sent"] = self.send_email_alert(alert_data)
        
        # 웹훅 알림 발송
        if self.config.webhook_enabled:
            results["webhook_sent"] = self.send_webhook_alert(alert_data)
        
        # 사용자 정의 알림
        results["custom_sent"] = self.send_custom_notification(alert_data, "alert")
        
        logger.info(f"알림 처리 완료: {alert_key} - 이메일: {results['email_sent']}, 웹훅: {results['webhook_sent']}")
        return results
    
    def test_notification_system(self) -> Dict:
        """알림 시스템 테스트"""
        test_alert = {
            "timestamp": datetime.now().isoformat(),
            "region": "테스트지역",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "risk_level": "high",
            "accidents": 8,
            "individuals": 12,
            "message": "🧪 알림 시스템 테스트 메시지입니다.",
            "recommended_actions": [
                "알림 시스템 정상 작동 확인",
                "수신자 설정 점검",
                "통신 연결 상태 확인"
            ]
        }
        
        logger.info("알림 시스템 테스트 시작...")
        results = self.process_alert(test_alert)
        logger.info(f"테스트 결과: {results}")
        
        return results

def create_notification_config() -> NotificationConfig:
    """알림 설정 생성"""
    config = NotificationConfig(
        email_enabled=True,
        webhook_enabled=True,
        alert_recipients=[
            "admin@example.com",
            "monitoring@example.com"
        ]
    )
    return config

def main():
    """메인 함수"""
    print("🔔 조류 충돌 모니터링 알림 시스템")
    print("=" * 50)
    
    # 설정 생성
    config = create_notification_config()
    notification_system = BirdCollisionNotificationSystem(config)
    
    # 테스트 실행
    print("알림 시스템 테스트를 실행하시겠습니까? (y/n): ", end="")
    if input().lower() == 'y':
        test_results = notification_system.test_notification_system()
        
        print("\n📊 테스트 결과:")
        print(f"  • 이메일 발송: {'✅ 성공' if test_results.get('email_sent') else '❌ 실패 (설정 확인 필요)'}")
        print(f"  • 웹훅 발송: {'✅ 성공' if test_results.get('webhook_sent') else '❌ 실패 (URL 확인 필요)'}")
        print(f"  • 로컬 저장: {'✅ 성공' if test_results.get('custom_sent') else '❌ 실패'}")
    
    # 실제 모니터링 데이터 처리
    print("\n실제 모니터링 데이터를 확인하시겠습니까? (y/n): ", end="")
    if input().lower() == 'y':
        try:
            with open('monitoring_report.json', 'r', encoding='utf-8') as f:
                monitoring_data = json.load(f)
            
            alerts = monitoring_data.get('active_alerts', [])
            if alerts:
                print(f"\n발견된 알림 {len(alerts)}개를 처리합니다...")
                for alert in alerts:
                    result = notification_system.process_alert(alert)
                    print(f"  • {alert['region']}: 처리 완료")
            else:
                print("\n현재 처리할 알림이 없습니다.")
                
        except FileNotFoundError:
            print("\n모니터링 데이터 파일을 찾을 수 없습니다.")
            print("먼저 integrated_monitoring_system.py를 실행하여 데이터를 생성하세요.")

if __name__ == "__main__":
    main()