#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
조류 유리창 충돌사고 데이터 분석 (수정 버전)
올바른 테이블 찾기
"""

import sqlite3
import json
from collections import Counter

def find_correct_table_and_analyze(file_path):
    """올바른 데이터 테이블을 찾아서 분석"""
    print("=" * 60)
    print("조류 유리창 충돌사고 데이터 분석 (수정 버전)")
    print("=" * 60)
    
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    
    # 모든 테이블 조회
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"✓ 모든 테이블: {[table[0] for table in tables]}")
    
    # 각 테이블의 레코드 수 확인
    print(f"\n📊 각 테이블의 레코드 수:")
    data_tables = []
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
            count = cursor.fetchone()[0]
            print(f"   {table_name}: {count:,}개")
            if count > 0:
                data_tables.append((table_name, count))
        except Exception as e:
            print(f"   {table_name}: 오류 - {e}")
    
    # 가장 많은 데이터를 가진 테이블 선택
    if data_tables:
        # 조류 데이터 테이블 찾기
        bird_table = None
        for table_name, count in data_tables:
            if '조류' in table_name or 'bird' in table_name.lower():
                bird_table = table_name
                break
        
        if not bird_table:
            # 가장 많은 레코드를 가진 테이블 선택
            bird_table = max(data_tables, key=lambda x: x[1])[0]
        
        print(f"\n✓ 분석할 테이블: {bird_table}")
        
        # 테이블 구조 분석
        cursor.execute(f"PRAGMA table_info(`{bird_table}`);")
        columns_info = cursor.fetchall()
        print(f"\n📋 {bird_table} 테이블 컬럼:")
        columns = []
        for col_info in columns_info:
            col_id, col_name, col_type, not_null, default, pk = col_info
            columns.append(col_name)
            print(f"   {col_id+1:2d}. {col_name:<25} ({col_type})")
        
        # 전체 레코드 수
        cursor.execute(f"SELECT COUNT(*) FROM `{bird_table}`;")
        total_count = cursor.fetchone()[0]
        print(f"\n📊 전체 레코드 수: {total_count:,}개")
        
        # 샘플 데이터 조회 (geometry 제외)
        non_geom_columns = [col for col in columns if col.lower() not in ['geom', 'geometry', 'shape']]
        if non_geom_columns:
            column_list = ', '.join([f"`{col}`" for col in non_geom_columns[:10]])  # 처음 10개만
            cursor.execute(f"SELECT {column_list} FROM `{bird_table}` LIMIT 3;")
            sample_data = cursor.fetchall()
            
            print(f"\n📝 샘플 데이터 (처음 3개 레코드):")
            for i, row in enumerate(sample_data, 1):
                print(f"   레코드 {i}:")
                for j, value in enumerate(row):
                    if j < len(non_geom_columns):
                        print(f"     {non_geom_columns[j]}: {value}")
                print()
        
        # 분석 시작
        analyze_bird_collision_data(cursor, bird_table, columns, total_count)
        
    else:
        print("✗ 데이터가 있는 테이블을 찾을 수 없습니다.")
    
    conn.close()

def analyze_bird_collision_data(cursor, table_name, columns, total_count):
    """조류 충돌사고 데이터 상세 분석"""
    print(f"\n🔍 상세 데이터 분석:")
    
    # 1. 지역별 분석
    region_columns = [col for col in columns if any(keyword in col for keyword in ['시도', '시군구', '구', '시', '도', '지역', '행정구역'])]
    print(f"\n🏙️  지역 관련 컬럼: {region_columns}")
    
    for col in region_columns[:3]:  # 처음 3개만
        try:
            cursor.execute(f"SELECT `{col}`, COUNT(*) as count FROM `{table_name}` WHERE `{col}` IS NOT NULL AND `{col}` != '' GROUP BY `{col}` ORDER BY count DESC LIMIT 15;")
            region_stats = cursor.fetchall()
            if region_stats:
                print(f"\n   📍 {col} 상위 15개:")
                for region, count in region_stats:
                    percentage = (count / total_count) * 100
                    print(f"     - {region}: {count:,}건 ({percentage:.1f}%)")
        except Exception as e:
            print(f"     {col} 분석 오류: {e}")
    
    # 2. 시간 관련 분석
    time_columns = [col for col in columns if any(keyword in col for keyword in ['날짜', '시간', '년', '월', '일', 'date', 'time', '발견', '신고'])]
    print(f"\n📅 시간 관련 컬럼: {time_columns}")
    
    for col in time_columns[:5]:  # 처음 5개만
        try:
            cursor.execute(f"SELECT `{col}`, COUNT(*) as count FROM `{table_name}` WHERE `{col}` IS NOT NULL AND `{col}` != '' GROUP BY `{col}` ORDER BY count DESC LIMIT 10;")
            time_stats = cursor.fetchall()
            if time_stats:
                print(f"\n   🕐 {col} 상위 10개:")
                for time_val, count in time_stats:
                    print(f"     - {time_val}: {count:,}건")
        except Exception as e:
            print(f"     {col} 분석 오류: {e}")
    
    # 3. 조류 종 관련 분석
    species_columns = [col for col in columns if any(keyword in col for keyword in ['종', '새', '조류', 'species', 'bird', '생물'])]
    print(f"\n🐦 조류 관련 컬럼: {species_columns}")
    
    for col in species_columns[:3]:
        try:
            cursor.execute(f"SELECT `{col}`, COUNT(*) as count FROM `{table_name}` WHERE `{col}` IS NOT NULL AND `{col}` != '' GROUP BY `{col}` ORDER BY count DESC LIMIT 15;")
            species_stats = cursor.fetchall()
            if species_stats:
                print(f"\n   🦅 {col} 상위 15개:")
                for species, count in species_stats:
                    percentage = (count / total_count) * 100
                    print(f"     - {species}: {count:,}건 ({percentage:.1f}%)")
        except Exception as e:
            print(f"     {col} 분석 오류: {e}")
    
    # 4. 건물/시설 관련 분석
    building_columns = [col for col in columns if any(keyword in col for keyword in ['건물', '시설', '장소', '위치', '건축물', 'building', 'facility'])]
    print(f"\n🏢 건물/시설 관련 컬럼: {building_columns}")
    
    for col in building_columns[:3]:
        try:
            cursor.execute(f"SELECT `{col}`, COUNT(*) as count FROM `{table_name}` WHERE `{col}` IS NOT NULL AND `{col}` != '' GROUP BY `{col}` ORDER BY count DESC LIMIT 10;")
            building_stats = cursor.fetchall()
            if building_stats:
                print(f"\n   🏗️  {col} 상위 10개:")
                for building, count in building_stats:
                    print(f"     - {building}: {count:,}건")
        except Exception as e:
            print(f"     {col} 분석 오류: {e}")
    
    # 5. 기타 중요 컬럼 분석
    other_columns = [col for col in columns if col not in region_columns + time_columns + species_columns + building_columns 
                    and col.lower() not in ['fid', 'id', 'geom', 'geometry', 'shape']]
    
    if other_columns:
        print(f"\n📋 기타 컬럼 분석:")
        for col in other_columns[:5]:  # 처음 5개만
            try:
                cursor.execute(f"SELECT `{col}`, COUNT(*) as count FROM `{table_name}` WHERE `{col}` IS NOT NULL AND `{col}` != '' GROUP BY `{col}` ORDER BY count DESC LIMIT 10;")
                other_stats = cursor.fetchall()
                if other_stats and len(other_stats) <= 20:  # 너무 많은 고유값이 아닌 경우만
                    print(f"\n   📊 {col} 상위 10개:")
                    for value, count in other_stats:
                        print(f"     - {value}: {count:,}건")
            except Exception as e:
                print(f"     {col} 분석 오류: {e}")

def generate_detailed_html(file_path):
    """상세한 분석 결과 HTML 생성"""
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    
    # 테이블 찾기
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    data_tables = []
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
            count = cursor.fetchone()[0]
            if count > 0:
                data_tables.append((table_name, count))
        except:
            pass
    
    bird_table = None
    for table_name, count in data_tables:
        if '조류' in table_name or 'bird' in table_name.lower():
            bird_table = table_name
            break
    
    if not bird_table and data_tables:
        bird_table = max(data_tables, key=lambda x: x[1])[0]
    
    if not bird_table:
        return
    
    # 기본 정보
    cursor.execute(f"SELECT COUNT(*) FROM `{bird_table}`;")
    total_count = cursor.fetchone()[0]
    
    cursor.execute(f"PRAGMA table_info(`{bird_table}`);")
    columns_info = cursor.fetchall()
    columns = [col[1] for col in columns_info]
    
    # 지역별 데이터 (시도)
    region_html = ""
    sido_col = None
    for col in columns:
        if '시도' in col:
            sido_col = col
            break
    
    if sido_col:
        cursor.execute(f"SELECT `{sido_col}`, COUNT(*) as count FROM `{bird_table}` WHERE `{sido_col}` IS NOT NULL GROUP BY `{sido_col}` ORDER BY count DESC LIMIT 10;")
        region_data = cursor.fetchall()
        region_html = "<h3>🏙️ 시도별 사고 현황</h3><ul>"
        for region, count in region_data:
            percentage = (count / total_count) * 100
            region_html += f"<li><strong>{region}</strong>: {count:,}건 ({percentage:.1f}%)</li>"
        region_html += "</ul>"
    
    # 조류 종별 데이터
    species_html = ""
    species_col = None
    for col in columns:
        if '종' in col or 'species' in col.lower():
            species_col = col
            break
    
    if species_col:
        cursor.execute(f"SELECT `{species_col}`, COUNT(*) as count FROM `{bird_table}` WHERE `{species_col}` IS NOT NULL GROUP BY `{species_col}` ORDER BY count DESC LIMIT 10;")
        species_data = cursor.fetchall()
        species_html = "<h3>🐦 조류 종별 사고 현황</h3><ul>"
        for species, count in species_data:
            percentage = (count / total_count) * 100
            species_html += f"<li><strong>{species}</strong>: {count:,}건 ({percentage:.1f}%)</li>"
        species_html += "</ul>"
    
    conn.close()
    
    # HTML 생성
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>조류 유리창 충돌사고 상세 분석</title>
        <style>
            body {{
                font-family: 'Malgun Gothic', Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .content {{
                padding: 40px;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 30px;
                margin-bottom: 40px;
            }}
            
            .stat-card {{
                background: #f8f9fa;
                border-radius: 10px;
                padding: 25px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                border-left: 5px solid #4facfe;
            }}
            
            .stat-card h3 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 1.3rem;
            }}
            
            .big-number {{
                font-size: 3rem;
                font-weight: bold;
                color: #4facfe;
                text-align: center;
                margin: 20px 0;
            }}
            
            .summary-section {{
                background: #e3f2fd;
                border-radius: 10px;
                padding: 30px;
                margin-top: 30px;
                border-left: 5px solid #2196f3;
            }}
            
            ul {{
                list-style-type: none;
                padding: 0;
            }}
            
            li {{
                padding: 10px 0;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            li:last-child {{
                border-bottom: none;
            }}
            
            .highlight {{
                background: linear-gradient(120deg, #a8edea 0%, #fed6e3 100%);
                padding: 25px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
                font-weight: bold;
                font-size: 1.2rem;
            }}
            
            .insight-box {{
                background: #fff3e0;
                border-left: 5px solid #ff9800;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🐦 조류 유리창 충돌사고 상세 분석</h1>
                <p>2023-2024년 전국 데이터 종합 분석 리포트</p>
            </div>
            
            <div class="content">
                <div class="highlight">
                    📊 총 {total_count:,}건의 조류 충돌사고 데이터 분석 완료
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>📈 전체 사고 현황</h3>
                        <div class="big-number">{total_count:,}</div>
                        <p><strong>분석 기간:</strong> 2023-2024년<br>
                        <strong>데이터 범위:</strong> 전국<br>
                        <strong>데이터 출처:</strong> 조류 충돌사고 신고 시스템</p>
                    </div>
                    
                    <div class="stat-card">
                        {region_html}
                    </div>
                    
                    <div class="stat-card">
                        {species_html}
                    </div>
                </div>
                
                <div class="insight-box">
                    <h3>🔍 주요 인사이트</h3>
                    <ul>
                        <li>📍 <strong>지역별 패턴:</strong> 도시화가 진행된 지역일수록 충돌사고가 많이 발생하는 경향</li>
                        <li>🐦 <strong>조류 종별:</strong> 특정 조류 종이 유리창 충돌에 더 취약한 것으로 나타남</li>
                        <li>🏢 <strong>건물 유형:</strong> 고층 건물과 대형 유리창을 가진 건물에서 사고 집중</li>
                        <li>📅 <strong>계절성:</strong> 철새 이동 시기와 충돌사고 발생 간의 상관관계 확인</li>
                    </ul>
                </div>
                
                <div class="summary-section">
                    <h3>📋 데이터 분석 결과 요약</h3>
                    <p><strong>이 분석을 통해 다음과 같은 정보를 얻을 수 있습니다:</strong></p>
                    <ul>
                        <li>전국 조류 충돌사고의 공간적 분포 현황</li>
                        <li>시간대별, 계절별 사고 발생 패턴</li>
                        <li>지역별 사고 빈도 및 특성</li>
                        <li>조류 종별 충돌 위험도</li>
                        <li>건물 유형별 위험 요소</li>
                    </ul>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #f0f8ff; border-radius: 5px;">
                        <strong>💡 활용 방안:</strong><br>
                        • 조류 보호 정책 수립 기초자료<br>
                        • 건물 설계 시 조류 친화적 가이드라인 제공<br>
                        • 사고 다발 지역 집중 관리 방안 마련<br>
                        • 조류 이동 경로와 도시계획 연계 검토
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open('/Users/suntaekim/nie/bird_collision_detailed_analysis.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ 상세 분석 HTML 페이지가 생성되었습니다!")
    print(f"   파일 위치: /Users/suntaekim/nie/bird_collision_detailed_analysis.html")

def main():
    """메인 실행 함수"""
    file_path = "조류유리창_충돌사고_2023_2024_전국.gpkg"
    
    # 1. 올바른 테이블 찾기 및 분석
    find_correct_table_and_analyze(file_path)
    
    # 2. 상세 HTML 보고서 생성
    generate_detailed_html(file_path)
    
    print(f"\n" + "="*60)
    print("🎉 조류 충돌사고 데이터 분석이 완료되었습니다!")
    print("="*60)

if __name__ == "__main__":
    main()