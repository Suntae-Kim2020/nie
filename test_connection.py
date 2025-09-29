#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL MCP 연결 테스트 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

def test_postgresql_connection():
    """PostgreSQL 연결 테스트"""
    try:
        # 연결 설정
        conn_params = {
            'host': 'localhost',
            'port': 5432,
            'database': 'bird_collision_db',
            'user': 'postgres',
            'password': 'password123'
        }
        
        print("🔌 PostgreSQL 연결 테스트 중...")
        
        # 연결 시도
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✅ 데이터베이스 연결 성공!")
        
        # 기본 쿼리 테스트
        test_queries = [
            {
                'name': '연결 확인',
                'query': 'SELECT version(), current_database(), current_user;'
            },
            {
                'name': '테이블 존재 확인',
                'query': "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
            },
            {
                'name': '데이터 건수 확인',
                'query': 'SELECT COUNT(*) as total_records FROM bird_collision_incidents;'
            },
            {
                'name': '샘플 데이터',
                'query': '''
                SELECT korean_common_name, province, facility_type, observation_date 
                FROM bird_collision_incidents 
                ORDER BY observation_date DESC 
                LIMIT 5;
                '''
            },
            {
                'name': '기본 통계',
                'query': '''
                SELECT 
                    COUNT(*) as 총_건수,
                    COUNT(DISTINCT korean_common_name) as 조류종_수,
                    COUNT(DISTINCT province) as 지역_수,
                    COUNT(DISTINCT facility_type) as 시설물_유형수
                FROM bird_collision_incidents;
                '''
            }
        ]
        
        results = {}
        
        for test in test_queries:
            try:
                print(f"\n📊 {test['name']} 테스트...")
                cursor.execute(test['query'])
                result = cursor.fetchall()
                results[test['name']] = [dict(row) for row in result]
                print(f"✅ 성공: {len(result)}개 결과")
                
                # 결과 출력 (처음 3개만)
                for i, row in enumerate(result[:3]):
                    print(f"   {i+1}: {dict(row)}")
                if len(result) > 3:
                    print(f"   ... (총 {len(result)}개)")
                    
            except Exception as e:
                print(f"❌ 실패: {e}")
                results[test['name']] = {'error': str(e)}
        
        # 결과를 JSON 파일로 저장
        test_result = {
            'timestamp': datetime.now().isoformat(),
            'connection_params': {k: v for k, v in conn_params.items() if k != 'password'},
            'test_results': results
        }
        
        with open('postgresql_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2, default=str)
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ 모든 테스트 완료!")
        print(f"📁 결과 저장: postgresql_test_results.json")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ 연결 실패: {e}")
        print("\n💡 해결 방법:")
        print("1. Docker 컨테이너가 실행 중인지 확인: docker-compose ps")
        print("2. PostgreSQL이 준비될 때까지 기다린 후 재시도")
        print("3. 포트 5432가 사용 가능한지 확인: lsof -i :5432")
        return False
        
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def generate_mcp_test_commands():
    """MCP 테스트용 명령어 생성"""
    
    commands = {
        "ChatGPT에서_사용할_수_있는_질의들": [
            "조류 충돌 사고 데이터베이스에서 총 몇 건의 사고가 기록되어 있나요?",
            "가장 많이 충돌하는 조류 종 상위 5개를 알려주세요",
            "지역별 사고 발생 건수를 내림차순으로 정렬해주세요", 
            "방음벽에서 발생한 사고는 전체의 몇 퍼센트인가요?",
            "계절별 사고 패턴을 분석해주세요",
            "버드세이버가 설치된 곳과 설치되지 않은 곳의 사고율 차이는?",
            "텃새와 철새 중 어느 쪽이 더 많이 충돌하나요?",
            "월별 사고 추이를 그래프로 보여주세요",
            "각 시도별로 가장 위험한 조류 종을 찾아주세요",
            "PostGIS를 사용해서 사고 핫스팟을 분석해주세요"
        ],
        
        "SQL_직접_실행_예시": [
            "SELECT COUNT(*) FROM bird_collision_incidents;",
            "SELECT korean_common_name, COUNT(*) as incidents FROM bird_collision_incidents GROUP BY korean_common_name ORDER BY incidents DESC LIMIT 10;",
            "SELECT province, COUNT(*) as incidents FROM bird_collision_incidents GROUP BY province ORDER BY incidents DESC;",
            "SELECT facility_type, COUNT(*) as incidents, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM bird_collision_incidents), 2) as percentage FROM bird_collision_incidents GROUP BY facility_type;",
            "SELECT * FROM get_seasonal_analysis();",
            "SELECT calculate_facility_risk_score('방음벽') as 방음벽_위험도;"
        ],
        
        "고급_분석_질의": [
            "지리적 클러스터링을 통해 사고 다발 지역을 찾아주세요",
            "시설물별 위험도 점수를 계산하고 순위를 매겨주세요", 
            "조류 종별로 선호하는 시설물과 계절 패턴을 교차분석해주세요",
            "반경 10km 내에서 발생한 사고들을 그룹화해주세요",
            "연도별 사고 증감률과 트렌드를 분석해주세요"
        ]
    }
    
    with open('mcp_test_commands.json', 'w', encoding='utf-8') as f:
        json.dump(commands, f, ensure_ascii=False, indent=2)
    
    print("📋 MCP 테스트 명령어 저장: mcp_test_commands.json")

if __name__ == "__main__":
    print("🧪 PostgreSQL MCP 연결 테스트")
    print("=" * 50)
    
    if test_postgresql_connection():
        generate_mcp_test_commands()
        print("\n🎯 다음 단계:")
        print("1. ChatGPT에서 MCP PostgreSQL 서버 연결")
        print("2. 생성된 테스트 명령어들로 질의 수행")
        print("3. mcp_test_commands.json 파일 참고")
    else:
        print("\n🔧 먼저 PostgreSQL 서버를 시작하세요:")
        print("docker-compose up -d")