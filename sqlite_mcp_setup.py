#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite MCP 테스트를 위한 데이터베이스 설정
기존 GeoPackage 데이터를 SQLite로 변환하여 MCP 테스트 준비
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os
import json

def create_sqlite_mcp_database():
    """MCP 테스트용 SQLite 데이터베이스 생성"""
    
    print("🐦 SQLite MCP 테스트 데이터베이스 생성 중...")
    
    # MCP 테스트용 새 데이터베이스 생성
    mcp_db_path = "bird_collision_mcp.db"
    
    # 기존 파일이 있으면 삭제
    if os.path.exists(mcp_db_path):
        os.remove(mcp_db_path)
        print(f"🗑️ 기존 파일 삭제: {mcp_db_path}")
    
    try:
        # 원본 GeoPackage에서 데이터 읽기
        source_conn = sqlite3.connect('조류유리창_충돌사고_2023_2024_전국.gpkg')
        
        # 전체 데이터 추출 (동정불가 제외)
        query = """
        SELECT 
            관찰번호 as observation_number,
            조사연도 as survey_year,
            관찰일자 as observation_date,
            등록일자 as registration_date,
            한글보통명 as korean_name,
            철새유형명 as migratory_type,
            서식지유형명 as habitat_type,
            학명 as scientific_name,
            영문보통명 as english_name,
            한글계명 as kingdom_ko,
            한글문명 as phylum_ko,
            한글강명 as class_ko,
            한글목명 as order_ko,
            한글과명 as family_ko,
            한글속명 as genus_ko,
            종 as species,
            CAST(위도 AS REAL) as latitude,
            CAST(경도 AS REAL) as longitude,
            CAST(개체수 AS INTEGER) as individual_count,
            시설물유형명 as facility_type,
            버드세이버여부 as bird_saver,
            시도명 as province
        FROM 조류유리창_충돌사고_2023_2024_전국
        WHERE 한글보통명 IS NOT NULL 
        AND 한글보통명 != '동정불가'
        AND 한글보통명 != ''
        ORDER BY 관찰일자, 시도명
        """
        
        df = pd.read_sql_query(query, source_conn)
        source_conn.close()
        
        print(f"✅ 원본 데이터 추출: {len(df):,}개 레코드")
        
        # 데이터 정리
        df['observation_date'] = pd.to_datetime(df['observation_date'], errors='coerce')
        df['registration_date'] = pd.to_datetime(df['registration_date'], errors='coerce')
        df['individual_count'] = df['individual_count'].fillna(1)
        
        # 결측값이 있는 중요 컬럼 제거
        df = df.dropna(subset=['korean_name', 'observation_date'])
        
        print(f"📊 정리 후 데이터: {len(df):,}개 레코드")
        
        # 새 SQLite 데이터베이스 생성
        mcp_conn = sqlite3.connect(mcp_db_path)
        cursor = mcp_conn.cursor()
        
        # 테이블 생성
        cursor.execute("""
        CREATE TABLE bird_collisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observation_number TEXT,
            survey_year INTEGER,
            observation_date DATE,
            registration_date DATE,
            korean_name TEXT NOT NULL,
            migratory_type TEXT,
            habitat_type TEXT,
            scientific_name TEXT,
            english_name TEXT,
            kingdom_ko TEXT,
            phylum_ko TEXT,
            class_ko TEXT,
            order_ko TEXT,
            family_ko TEXT,
            genus_ko TEXT,
            species TEXT,
            latitude REAL,
            longitude REAL,
            individual_count INTEGER DEFAULT 1,
            facility_type TEXT,
            bird_saver TEXT,
            province TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 인덱스 생성
        indexes = [
            "CREATE INDEX idx_observation_date ON bird_collisions(observation_date)",
            "CREATE INDEX idx_korean_name ON bird_collisions(korean_name)",
            "CREATE INDEX idx_province ON bird_collisions(province)",
            "CREATE INDEX idx_facility_type ON bird_collisions(facility_type)",
            "CREATE INDEX idx_migratory_type ON bird_collisions(migratory_type)",
            "CREATE INDEX idx_survey_year ON bird_collisions(survey_year)",
            "CREATE INDEX idx_location ON bird_collisions(latitude, longitude)"
        ]
        
        for index in indexes:
            cursor.execute(index)
        
        print("📋 테이블 및 인덱스 생성 완료")
        
        # 데이터 삽입
        df.to_sql('bird_collisions', mcp_conn, if_exists='replace', index=False)
        
        # 통계 뷰 생성
        cursor.execute("""
        CREATE VIEW species_statistics AS
        SELECT 
            korean_name,
            migratory_type,
            COUNT(*) as incident_count,
            SUM(individual_count) as total_individuals,
            COUNT(DISTINCT province) as affected_provinces,
            COUNT(DISTINCT facility_type) as facility_types,
            MIN(observation_date) as first_incident,
            MAX(observation_date) as latest_incident,
            ROUND(AVG(individual_count), 2) as avg_individuals_per_incident
        FROM bird_collisions
        GROUP BY korean_name, migratory_type
        ORDER BY incident_count DESC
        """)
        
        cursor.execute("""
        CREATE VIEW province_statistics AS
        SELECT 
            province,
            COUNT(*) as total_incidents,
            COUNT(DISTINCT korean_name) as species_count,
            SUM(individual_count) as total_individuals,
            COUNT(DISTINCT facility_type) as facility_types,
            ROUND(AVG(individual_count), 2) as avg_individuals,
            GROUP_CONCAT(DISTINCT korean_name) as top_species
        FROM bird_collisions
        GROUP BY province
        ORDER BY total_incidents DESC
        """)
        
        cursor.execute("""
        CREATE VIEW monthly_trends AS
        SELECT 
            strftime('%Y', observation_date) as year,
            strftime('%m', observation_date) as month,
            COUNT(*) as incidents,
            COUNT(DISTINCT korean_name) as species_count,
            SUM(individual_count) as total_individuals,
            COUNT(DISTINCT province) as affected_provinces
        FROM bird_collisions
        WHERE observation_date IS NOT NULL
        GROUP BY strftime('%Y', observation_date), strftime('%m', observation_date)
        ORDER BY year, month
        """)
        
        cursor.execute("""
        CREATE VIEW facility_analysis AS
        SELECT 
            facility_type,
            COUNT(*) as incidents,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM bird_collisions), 2) as percentage,
            COUNT(DISTINCT korean_name) as species_affected,
            SUM(individual_count) as total_individuals,
            COUNT(DISTINCT province) as provinces_affected,
            SUM(CASE WHEN bird_saver = 'Y' THEN 1 ELSE 0 END) as with_bird_saver,
            SUM(CASE WHEN bird_saver = 'N' THEN 1 ELSE 0 END) as without_bird_saver
        FROM bird_collisions
        WHERE facility_type IS NOT NULL
        GROUP BY facility_type
        ORDER BY incidents DESC
        """)
        
        # 계절별 분석 뷰
        cursor.execute("""
        CREATE VIEW seasonal_analysis AS
        SELECT 
            CASE 
                WHEN CAST(strftime('%m', observation_date) AS INTEGER) IN (3,4,5) THEN '봄'
                WHEN CAST(strftime('%m', observation_date) AS INTEGER) IN (6,7,8) THEN '여름'
                WHEN CAST(strftime('%m', observation_date) AS INTEGER) IN (9,10,11) THEN '가을'
                ELSE '겨울'
            END as season,
            COUNT(*) as incidents,
            COUNT(DISTINCT korean_name) as species_count,
            SUM(individual_count) as total_individuals,
            COUNT(DISTINCT province) as affected_provinces
        FROM bird_collisions
        WHERE observation_date IS NOT NULL
        GROUP BY season
        ORDER BY incidents DESC
        """)
        
        # 커밋 및 연결 종료
        mcp_conn.commit()
        
        # 최종 통계 출력
        cursor.execute("SELECT COUNT(*) FROM bird_collisions")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT korean_name) FROM bird_collisions")
        species_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT province) FROM bird_collisions")
        province_count = cursor.fetchone()[0]
        
        mcp_conn.close()
        
        # 파일 크기 확인
        file_size = os.path.getsize(mcp_db_path) / (1024 * 1024)  # MB
        
        print(f"✅ SQLite MCP 데이터베이스 생성 완료!")
        print(f"📁 파일: {mcp_db_path}")
        print(f"💾 크기: {file_size:.2f} MB")
        print(f"📊 레코드: {total_records:,}개")
        print(f"🐦 조류 종: {species_count}개")
        print(f"🗺️ 지역: {province_count}개")
        
        return mcp_db_path
        
    except Exception as e:
        print(f"❌ 데이터베이스 생성 실패: {e}")
        return None

def create_mcp_test_queries():
    """MCP 테스트용 쿼리 생성"""
    
    queries = {
        "basic_stats": {
            "description": "기본 통계 조회",
            "query": """
            SELECT 
                COUNT(*) as total_incidents,
                COUNT(DISTINCT korean_name) as species_count,
                COUNT(DISTINCT province) as province_count,
                SUM(individual_count) as total_individuals,
                MIN(observation_date) as first_date,
                MAX(observation_date) as latest_date
            FROM bird_collisions;
            """
        },
        
        "top_dangerous_species": {
            "description": "가장 위험한 조류 종 TOP 10",
            "query": """
            SELECT 
                korean_name,
                migratory_type,
                incident_count,
                total_individuals,
                affected_provinces
            FROM species_statistics
            LIMIT 10;
            """
        },
        
        "province_ranking": {
            "description": "지역별 사고 순위",
            "query": """
            SELECT 
                province,
                total_incidents,
                species_count,
                total_individuals,
                top_species
            FROM province_statistics;
            """
        },
        
        "facility_analysis": {
            "description": "시설물별 분석",
            "query": """
            SELECT 
                facility_type,
                incidents,
                percentage,
                species_affected,
                with_bird_saver,
                without_bird_saver
            FROM facility_analysis;
            """
        },
        
        "monthly_trends": {
            "description": "월별 사고 추이",
            "query": """
            SELECT 
                year,
                month,
                incidents,
                species_count,
                total_individuals
            FROM monthly_trends
            ORDER BY year, month;
            """
        },
        
        "seasonal_patterns": {
            "description": "계절별 패턴 분석",
            "query": """
            SELECT * FROM seasonal_analysis;
            """
        },
        
        "bird_saver_effectiveness": {
            "description": "버드세이버 효과 분석",
            "query": """
            SELECT 
                bird_saver,
                COUNT(*) as incidents,
                COUNT(DISTINCT korean_name) as species_count,
                AVG(individual_count) as avg_individuals,
                COUNT(DISTINCT province) as provinces
            FROM bird_collisions
            WHERE bird_saver IN ('Y', 'N')
            GROUP BY bird_saver;
            """
        },
        
        "migratory_vs_resident": {
            "description": "철새 vs 텃새 분석",
            "query": """
            SELECT 
                migratory_type,
                COUNT(*) as incidents,
                COUNT(DISTINCT korean_name) as species_count,
                SUM(individual_count) as total_individuals,
                COUNT(DISTINCT province) as affected_provinces
            FROM bird_collisions
            WHERE migratory_type IS NOT NULL
            GROUP BY migratory_type
            ORDER BY incidents DESC;
            """
        },
        
        "geographic_hotspots": {
            "description": "지리적 핫스팟 분석",
            "query": """
            SELECT 
                province,
                korean_name,
                COUNT(*) as incidents,
                AVG(latitude) as avg_lat,
                AVG(longitude) as avg_lng,
                facility_type
            FROM bird_collisions
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY province, korean_name, facility_type
            HAVING incidents >= 5
            ORDER BY incidents DESC
            LIMIT 20;
            """
        },
        
        "yearly_comparison": {
            "description": "연도별 비교 분석",
            "query": """
            SELECT 
                survey_year,
                COUNT(*) as incidents,
                COUNT(DISTINCT korean_name) as species_count,
                COUNT(DISTINCT province) as affected_provinces,
                SUM(individual_count) as total_individuals
            FROM bird_collisions
            GROUP BY survey_year
            ORDER BY survey_year;
            """
        }
    }
    
    # 개별 쿼리 파일 생성
    for query_name, query_info in queries.items():
        filename = f"sqlite_mcp_query_{query_name}.sql"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"-- SQLite MCP 테스트 쿼리: {query_info['description']}\n")
            f.write(f"-- 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(query_info['query'])
        
        print(f"📝 쿼리 파일 생성: {filename}")
    
    # JSON 형태로도 저장
    with open("sqlite_mcp_queries.json", "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)
    
    print("📚 통합 쿼리 파일 생성: sqlite_mcp_queries.json")
    
    return queries

def test_sqlite_connection(db_path):
    """SQLite 연결 및 기본 테스트"""
    
    try:
        print(f"🔌 SQLite 연결 테스트: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 기본 테스트들
        tests = [
            ("테이블 목록", "SELECT name FROM sqlite_master WHERE type='table';"),
            ("뷰 목록", "SELECT name FROM sqlite_master WHERE type='view';"),
            ("전체 레코드 수", "SELECT COUNT(*) FROM bird_collisions;"),
            ("샘플 데이터", "SELECT korean_name, province, facility_type, observation_date FROM bird_collisions LIMIT 3;")
        ]
        
        results = {}
        
        for test_name, query in tests:
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                results[test_name] = result
                print(f"✅ {test_name}: {len(result)}개 결과")
                
                # 처음 3개 결과만 출력
                for i, row in enumerate(result[:3]):
                    print(f"   {i+1}: {row}")
                if len(result) > 3:
                    print(f"   ... (총 {len(result)}개)")
                    
            except Exception as e:
                print(f"❌ {test_name} 실패: {e}")
                results[test_name] = {"error": str(e)}
        
        conn.close()
        
        # 결과 저장
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "database_path": db_path,
            "test_results": results
        }
        
        with open("sqlite_mcp_test_results.json", "w", encoding="utf-8") as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2, default=str)
        
        print("✅ SQLite 연결 테스트 완료!")
        print("📁 결과 저장: sqlite_mcp_test_results.json")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite 연결 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("🧪 SQLite MCP 테스트 환경 설정")
    print("=" * 60)
    
    # 1. MCP 테스트용 SQLite 데이터베이스 생성
    db_path = create_sqlite_mcp_database()
    
    if db_path:
        # 2. 테스트 쿼리 생성
        create_mcp_test_queries()
        
        # 3. 연결 테스트
        test_sqlite_connection(db_path)
        
        print("\n✅ SQLite MCP 테스트 환경 준비 완료!")
        print(f"\n📋 다음 단계:")
        print(f"1. 생성된 데이터베이스: {db_path}")
        print(f"2. ChatGPT MCP SQLite 서버 설정")
        print(f"3. 생성된 쿼리들로 테스트 수행")
        print(f"4. sqlite_mcp_queries.json 파일 참고")
    else:
        print("\n❌ 환경 설정 실패")