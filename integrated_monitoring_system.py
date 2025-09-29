#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 조류 충돌 모니터링 시스템
실시간 데이터 수집, 분석, 예측 및 알림 기능을 제공
"""

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import time
from collections import defaultdict
# import requests  # Optional for web requests
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BirdCollisionMonitoringSystem:
    def __init__(self, db_path="조류유리창_충돌사고_2023_2024_전국.gpkg"):
        self.db_path = db_path
        self.monitoring_data = {}
        self.risk_thresholds = {
            'critical': 10,  # 일일 10건 이상
            'high': 5,       # 일일 5-9건
            'medium': 2,     # 일일 2-4건
            'low': 1         # 일일 1건
        }
        self.setup_monitoring_system()
    
    def setup_monitoring_system(self):
        """모니터링 시스템 초기화"""
        logger.info("조류 충돌 모니터링 시스템 초기화 중...")
        
        # 데이터베이스 연결 테스트
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                logger.info(f"데이터베이스 테이블: {tables}")
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
    
    def get_real_time_data(self):
        """실시간 데이터 수집 (시뮬레이션)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 최근 7일 데이터 조회
                query = """
                SELECT 
                    시도명, 한글보통명 as 종명, 개체수,
                    위도, 경도, 관찰일자, 시설물유형명,
                    버드세이버여부, 철새유형명
                FROM 조류유리창_충돌사고_2023_2024_전국 
                WHERE julianday('now') - julianday(관찰일자) <= 7
                ORDER BY 관찰일자 DESC
                """
                df = pd.read_sql_query(query, conn)
                
                # 일별 사고 집계
                df['발견일'] = pd.to_datetime(df['관찰일자'], errors='coerce').dt.date
                daily_stats = df.groupby(['발견일', '시도명']).agg({
                    '종명': 'count',
                    '개체수': 'sum'
                }).rename(columns={'종명': '사고건수'}).reset_index()
                
                return df, daily_stats
                
        except Exception as e:
            logger.error(f"실시간 데이터 수집 실패: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def analyze_risk_levels(self, daily_stats):
        """위험도 수준 분석"""
        risk_analysis = {}
        
        for _, row in daily_stats.iterrows():
            region = row['시도명']
            accidents = row['사고건수']
            
            if accidents >= self.risk_thresholds['critical']:
                level = 'critical'
            elif accidents >= self.risk_thresholds['high']:
                level = 'high'
            elif accidents >= self.risk_thresholds['medium']:
                level = 'medium'
            else:
                level = 'low'
            
            if region not in risk_analysis:
                risk_analysis[region] = []
            
            risk_analysis[region].append({
                'date': str(row['발견일']),
                'accidents': accidents,
                'individuals': row['개체수'],
                'risk_level': level
            })
        
        return risk_analysis
    
    def generate_alerts(self, risk_analysis):
        """경고 알림 생성"""
        alerts = []
        current_date = datetime.now().date()
        
        for region, data in risk_analysis.items():
            for entry in data:
                if entry['risk_level'] in ['critical', 'high']:
                    alert = {
                        'timestamp': datetime.now().isoformat(),
                        'region': region,
                        'date': entry['date'],
                        'risk_level': entry['risk_level'],
                        'accidents': entry['accidents'],
                        'individuals': entry['individuals'],
                        'message': self.create_alert_message(region, entry),
                        'recommended_actions': self.get_recommended_actions(entry['risk_level'])
                    }
                    alerts.append(alert)
        
        return alerts
    
    def create_alert_message(self, region, entry):
        """경고 메시지 생성"""
        if entry['risk_level'] == 'critical':
            return f"🚨 긴급: {region}에서 {entry['date']}일 {entry['accidents']}건의 조류 충돌 사고 발생 (개체수: {entry['individuals']}마리)"
        elif entry['risk_level'] == 'high':
            return f"⚠️ 주의: {region}에서 {entry['date']}일 {entry['accidents']}건의 조류 충돌 사고 발생 (개체수: {entry['individuals']}마리)"
        else:
            return f"ℹ️ 정보: {region}에서 {entry['date']}일 {entry['accidents']}건의 조류 충돌 사고 발생"
    
    def get_recommended_actions(self, risk_level):
        """권장 조치사항"""
        actions = {
            'critical': [
                "즉시 현장 조사팀 파견",
                "임시 방음벽 설치 또는 기존 방음벽 보완",
                "조류 유도 장치 긴급 설치",
                "지역 주민 및 관련 기관 통보",
                "연속 3일간 집중 모니터링"
            ],
            'high': [
                "24시간 내 현장 점검",
                "조류 회피 장치 점검 및 보완",
                "주변 환경 요인 조사",
                "예방 조치 강화"
            ],
            'medium': [
                "주간 현장 점검 계획 수립",
                "기존 예방 시설 점검",
                "모니터링 빈도 증가"
            ],
            'low': [
                "정기 점검 일정 유지",
                "예방 교육 실시"
            ]
        }
        return actions.get(risk_level, [])
    
    def predict_hotspots(self, df):
        """사고 다발 지역 예측"""
        # 지역별 최근 사고 패턴 분석
        location_stats = df.groupby('시도명').agg({
            '종명': 'count',
            '개체수': 'sum',
            '시설물유형명': lambda x: x.mode().iloc[0] if not x.empty else ''
        }).rename(columns={'종명': '사고건수'}).reset_index()
        
        # 위험도 점수 계산
        location_stats['위험도점수'] = (
            location_stats['사고건수'] * 2 + 
            location_stats['개체수'] * 1.5
        )
        
        # 상위 위험 지역 선별
        hotspots = location_stats.nlargest(10, '위험도점수').to_dict('records')
        
        return hotspots
    
    def generate_prevention_recommendations(self, hotspots, alerts):
        """예방 조치 권고사항 생성"""
        recommendations = {
            'immediate_actions': [],
            'short_term_plans': [],
            'long_term_strategies': []
        }
        
        # 즉시 조치사항
        for alert in alerts:
            if alert['risk_level'] == 'critical':
                recommendations['immediate_actions'].append({
                    'region': alert['region'],
                    'action': '긴급 현장 대응팀 파견',
                    'priority': 'critical',
                    'deadline': '24시간 이내'
                })
        
        # 단기 계획
        for hotspot in hotspots[:5]:
            recommendations['short_term_plans'].append({
                'region': hotspot['시도명'],
                'action': '집중 모니터링 및 예방 시설 보강',
                'priority': 'high',
                'deadline': '1개월 이내'
            })
        
        # 장기 전략
        recommendations['long_term_strategies'] = [
            {
                'action': '조류 친화적 건축 설계 기준 강화',
                'priority': 'medium',
                'deadline': '6개월 이내'
            },
            {
                'action': '전국 단위 실시간 모니터링 네트워크 구축',
                'priority': 'medium',
                'deadline': '1년 이내'
            },
            {
                'action': '조류 이동 경로 기반 도시계획 수립',
                'priority': 'low',
                'deadline': '2년 이내'
            }
        ]
        
        return recommendations
    
    def create_monitoring_report(self):
        """모니터링 보고서 생성"""
        logger.info("모니터링 보고서 생성 중...")
        
        # 실시간 데이터 수집
        df, daily_stats = self.get_real_time_data()
        
        if df.empty:
            logger.warning("수집된 데이터가 없습니다.")
            return None
        
        # 위험도 분석
        risk_analysis = self.analyze_risk_levels(daily_stats)
        
        # 경고 알림 생성
        alerts = self.generate_alerts(risk_analysis)
        
        # 사고 다발 지역 예측
        hotspots = self.predict_hotspots(df)
        
        # 예방 조치 권고
        recommendations = self.generate_prevention_recommendations(hotspots, alerts)
        
        # 전체 보고서 구성
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'data_period': '최근 7일',
                'total_records': len(df),
                'monitoring_regions': df['시도명'].nunique()
            },
            'current_status': {
                'total_accidents_week': len(df),
                'total_individuals': df['개체수'].sum(),
                'affected_regions': df['시도명'].nunique(),
                'main_facilities': df['시설물구분'].value_counts().head(3).to_dict()
            },
            'risk_analysis': risk_analysis,
            'active_alerts': alerts,
            'predicted_hotspots': hotspots,
            'recommendations': recommendations,
            'daily_statistics': daily_stats.to_dict('records')
        }
        
        # JSON 파일로 저장
        with open('monitoring_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"모니터링 보고서 생성 완료: {len(alerts)}개 알림, {len(hotspots)}개 위험지역")
        return report
    
    def run_continuous_monitoring(self, interval_minutes=60):
        """연속 모니터링 실행"""
        logger.info(f"연속 모니터링 시작 (간격: {interval_minutes}분)")
        
        while True:
            try:
                report = self.create_monitoring_report()
                
                if report and report['active_alerts']:
                    logger.warning(f"활성 알림 {len(report['active_alerts'])}개 발생")
                    for alert in report['active_alerts']:
                        logger.warning(alert['message'])
                
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("모니터링 시스템 종료")
                break
            except Exception as e:
                logger.error(f"모니터링 중 오류 발생: {e}")
                time.sleep(300)  # 5분 대기 후 재시도

def main():
    """메인 함수"""
    monitor = BirdCollisionMonitoringSystem()
    
    # 단일 보고서 생성
    report = monitor.create_monitoring_report()
    
    if report:
        print("=" * 60)
        print("🐦 조류 충돌 모니터링 시스템 보고서")
        print("=" * 60)
        print(f"📊 분석 기간: {report['report_metadata']['data_period']}")
        print(f"📈 총 사고 건수: {report['current_status']['total_accidents_week']}건")
        print(f"🔴 활성 알림: {len(report['active_alerts'])}개")
        print(f"⚠️ 위험 지역: {len(report['predicted_hotspots'])}곳")
        
        if report['active_alerts']:
            print("\n🚨 긴급 알림:")
            for alert in report['active_alerts'][:5]:
                print(f"  • {alert['message']}")
        
        print(f"\n📄 상세 보고서가 'monitoring_report.json'에 저장되었습니다.")
    
    # 연속 모니터링은 별도 실행

if __name__ == "__main__":
    main()