#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
조류 충돌 데이터를 PostgreSQL에 삽입하는 스크립트
MCP 테스트용 데이터 준비
"""

import pandas as pd
import sqlite3
from datetime import datetime
import re

def generate_postgresql_insert_script():
    """SQLite 데이터를 PostgreSQL INSERT 스크립트로 변환"""
    
    print("🐦 PostgreSQL INSERT 스크립트 생성 중...")
    
    try:
        # SQLite에서 데이터 읽기
        conn = sqlite3.connect('조류유리창_충돌사고_2023_2024_전국.gpkg')
        
        query = """
        SELECT 
            관찰번호,
            조사연도,
            관찰일자,
            등록일자,
            한글보통명,
            철새유형명,
            서식지유형명,
            학명,
            영문보통명,
            한글계명,
            한글문명,
            한글강명,
            한글목명,
            한글과명,
            한글속명,
            종,
            위도,
            경도,
            개체수,
            시설물유형명,
            버드세이버여부,
            시도명
        FROM 조류유리창_충돌사고_2023_2024_전국
        WHERE 한글보통명 IS NOT NULL AND 한글보통명 != '동정불가'
        ORDER BY 관찰일자, 시도명
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"✅ 데이터 추출 완료: {len(df):,}개 레코드")
        
        # 데이터 정리
        df['관찰일자'] = pd.to_datetime(df['관찰일자'], errors='coerce')
        df['등록일자'] = pd.to_datetime(df['등록일자'], errors='coerce')
        df['개체수'] = pd.to_numeric(df['개체수'], errors='coerce').fillna(1)
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        
        # 결측값 처리
        df = df.dropna(subset=['한글보통명', '관찰일자'])
        
        print(f"📊 정리 후 데이터: {len(df):,}개 레코드")
        
        # PostgreSQL INSERT 스크립트 생성
        insert_script = []
        insert_script.append("-- PostgreSQL 조류 충돌 데이터 삽입 스크립트")
        insert_script.append("-- 생성일: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        insert_script.append("")
        insert_script.append("-- 데이터베이스 연결")
        insert_script.append("\\c bird_collision_db;")
        insert_script.append("")
        insert_script.append("-- 데이터 삽입 시작")
        insert_script.append("BEGIN;")
        insert_script.append("")
        
        # 배치 단위로 INSERT 문 생성
        batch_size = 1000
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]
            
            insert_script.append(f"-- 배치 {batch_num + 1}/{total_batches} ({len(batch_df)}개 레코드)")
            insert_script.append("INSERT INTO bird_collision_incidents (")
            insert_script.append("    observation_number, survey_year, observation_date, registration_date,")
            insert_script.append("    korean_common_name, migratory_type, habitat_type, scientific_name,")
            insert_script.append("    english_name, taxonomy_kingdom, taxonomy_phylum, taxonomy_class,")
            insert_script.append("    taxonomy_order, taxonomy_family, taxonomy_genus, taxonomy_species,")
            insert_script.append("    latitude, longitude, individual_count, facility_type,")
            insert_script.append("    bird_saver_installed, province")
            insert_script.append(") VALUES")
            
            values = []
            for _, row in batch_df.iterrows():
                # NULL 값과 특수문자 처리
                def clean_value(val):
                    if pd.isna(val) or val is None:
                        return "NULL"
                    if isinstance(val, str):
                        # SQL 인젝션 방지 및 특수문자 이스케이프
                        val = val.replace("'", "''").replace("\\", "\\\\")
                        return f"'{val}'"
                    return str(val)
                
                def clean_date(date_val):
                    if pd.isna(date_val):
                        return "NULL"
                    return f"'{date_val.strftime('%Y-%m-%d')}'"
                
                def clean_bool(bool_val):
                    if pd.isna(bool_val) or bool_val is None:
                        return "NULL"
                    return "TRUE" if str(bool_val).upper() in ['Y', 'YES', 'TRUE', '1'] else "FALSE"
                
                value_str = f"""({clean_value(row['관찰번호'])}, {clean_value(row['조사연도'])}, 
{clean_date(row['관찰일자'])}, {clean_date(row['등록일자'])}, 
{clean_value(row['한글보통명'])}, {clean_value(row['철새유형명'])}, 
{clean_value(row['서식지유형명'])}, {clean_value(row['학명'])}, 
{clean_value(row['영문보통명'])}, {clean_value(row['한글계명'])}, 
{clean_value(row['한글문명'])}, {clean_value(row['한글강명'])}, 
{clean_value(row['한글목명'])}, {clean_value(row['한글과명'])}, 
{clean_value(row['한글속명'])}, {clean_value(row['종'])}, 
{clean_value(row['위도'])}, {clean_value(row['경도'])}, 
{clean_value(row['개체수'])}, {clean_value(row['시설물유형명'])}, 
{clean_bool(row['버드세이버여부'])}, {clean_value(row['시도명'])})"""
                
                values.append(value_str)
            
            insert_script.append(",\n".join(values) + ";")
            insert_script.append("")
        
        insert_script.append("COMMIT;")
        insert_script.append("")
        insert_script.append("-- 통계 업데이트")
        insert_script.append("ANALYZE bird_collision_incidents;")
        insert_script.append("")
        insert_script.append("-- 삽입 완료 확인")
        insert_script.append("SELECT COUNT(*) as total_records FROM bird_collision_incidents;")
        insert_script.append("SELECT province, COUNT(*) as incidents FROM bird_collision_incidents GROUP BY province ORDER BY incidents DESC;")
        
        # 파일로 저장
        script_content = "\n".join(insert_script)
        with open("insert_bird_collision_data.sql", "w", encoding="utf-8") as f:
            f.write(script_content)
        
        print(f"📁 PostgreSQL INSERT 스크립트 생성 완료:")
        print(f"   파일명: insert_bird_collision_data.sql")
        print(f"   크기: {len(script_content):,} 문자")
        print(f"   배치 수: {total_batches}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 스크립트 생성 실패: {e}")
        return False

def create_mcp_test_queries():
    """MCP 테스트용 쿼리 모음 생성"""
    
    queries = {
        "기본_통계": """
-- 전체 통계 조회
SELECT 
    COUNT(*) as 총_사고건수,
    COUNT(DISTINCT korean_common_name) as 조류종_수,
    COUNT(DISTINCT province) as 시도_수,
    SUM(individual_count) as 총_개체수
FROM bird_collision_incidents;
""",
        
        "위험_조류_TOP10": """
-- 가장 위험한 조류 종 TOP 10
SELECT 
    korean_common_name as 조류종,
    COUNT(*) as 사고건수,
    SUM(individual_count) as 총_개체수,
    migratory_type as 철새유형,
    ROUND(AVG(individual_count), 2) as 평균_개체수
FROM bird_collision_incidents
GROUP BY korean_common_name, migratory_type
ORDER BY 사고건수 DESC
LIMIT 10;
""",
        
        "지역별_위험도": """
-- 지역별 사고 위험도 순위
SELECT 
    province as 시도,
    COUNT(*) as 사고건수,
    COUNT(DISTINCT korean_common_name) as 조류종_다양성,
    COUNT(DISTINCT facility_type) as 시설물_유형수,
    ROUND(calculate_facility_risk_score('방음벽'), 2) as 방음벽_위험도,
    array_agg(DISTINCT korean_common_name ORDER BY korean_common_name) as 주요_조류종
FROM bird_collision_incidents
GROUP BY province
ORDER BY 사고건수 DESC;
""",
        
        "시설물별_분석": """
-- 시설물별 상세 분석
SELECT 
    facility_type as 시설물유형,
    COUNT(*) as 사고건수,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM bird_collision_incidents)), 2) as 비율_퍼센트,
    COUNT(DISTINCT korean_common_name) as 영향받은_조류종수,
    AVG(individual_count) as 평균_개체수,
    SUM(CASE WHEN bird_saver_installed THEN 1 ELSE 0 END) as 버드세이버_설치건수
FROM bird_collision_incidents
GROUP BY facility_type
ORDER BY 사고건수 DESC;
""",
        
        "계절별_패턴": """
-- 계절별 사고 패턴 분석
SELECT * FROM get_seasonal_analysis();
""",
        
        "월별_트렌드": """
-- 월별 사고 트렌드
SELECT 
    EXTRACT(MONTH FROM observation_date) as 월,
    COUNT(*) as 사고건수,
    COUNT(DISTINCT korean_common_name) as 조류종수,
    array_agg(DISTINCT korean_common_name ORDER BY korean_common_name) as 주요_종들
FROM bird_collision_incidents
GROUP BY EXTRACT(MONTH FROM observation_date)
ORDER BY 월;
""",
        
        "버드세이버_효과": """
-- 버드세이버 설치 효과 분석
SELECT 
    bird_saver_installed as 버드세이버_설치여부,
    COUNT(*) as 사고건수,
    AVG(individual_count) as 평균_개체수,
    COUNT(DISTINCT korean_common_name) as 영향받은_종수
FROM bird_collision_incidents
WHERE bird_saver_installed IS NOT NULL
GROUP BY bird_saver_installed;
""",
        
        "핫스팟_분석": """
-- 지역별 핫스팟 분석 (PostGIS 활용)
SELECT 
    province as 시도,
    total_incidents as 총_사고건수,
    ST_AsText(center_point) as 중심좌표,
    array_length(species_list, 1) as 조류종_수
FROM v_regional_hotspots
ORDER BY total_incidents DESC;
""",
        
        "철새vs텃새": """
-- 철새 vs 텃새 충돌 패턴 비교
SELECT 
    migratory_type as 철새유형,
    COUNT(*) as 사고건수,
    COUNT(DISTINCT korean_common_name) as 종_다양성,
    COUNT(DISTINCT province) as 영향지역수,
    AVG(individual_count) as 평균_개체수
FROM bird_collision_incidents
WHERE migratory_type IS NOT NULL
GROUP BY migratory_type
ORDER BY 사고건수 DESC;
"""
    }
    
    # 쿼리 파일들 생성
    for query_name, query_sql in queries.items():
        filename = f"mcp_test_query_{query_name}.sql"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"-- MCP 테스트 쿼리: {query_name}\n")
            f.write(f"-- 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(query_sql)
        
        print(f"📝 쿼리 파일 생성: {filename}")
    
    # 통합 쿼리 파일 생성
    with open("mcp_test_all_queries.sql", "w", encoding="utf-8") as f:
        f.write("-- PostgreSQL MCP 테스트용 전체 쿼리 모음\n")
        f.write(f"-- 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for query_name, query_sql in queries.items():
            f.write(f"-- ============================================\n")
            f.write(f"-- {query_name.replace('_', ' ').upper()}\n")
            f.write(f"-- ============================================\n")
            f.write(query_sql)
            f.write("\n\n")
    
    print("📚 통합 쿼리 파일 생성: mcp_test_all_queries.sql")

if __name__ == "__main__":
    print("🔧 PostgreSQL MCP 테스트 준비")
    print("=" * 60)
    
    if generate_postgresql_insert_script():
        create_mcp_test_queries()
        print("\n✅ PostgreSQL MCP 테스트 준비 완료!")
        print("\n📋 다음 단계:")
        print("1. PostgreSQL 서버에 postgresql_mcp_setup.sql 실행")
        print("2. insert_bird_collision_data.sql로 데이터 삽입")
        print("3. MCP 서버 설정 및 연결")
        print("4. 생성된 쿼리들로 ChatGPT에서 테스트")
    else:
        print("\n❌ 준비 실패")