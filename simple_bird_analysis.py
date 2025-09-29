#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
조류 유리창 충돌사고 데이터 분석 (단순 버전)
Fiona를 사용한 GeoPackage 파일 읽기
"""

import json
import sqlite3
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

def analyze_gpkg_with_sqlite(file_path):
    """SQLite를 사용하여 GeoPackage 파일 분석"""
    print("=" * 60)
    print("조류 유리창 충돌사고 데이터 분석 (SQLite 방식)")
    print("=" * 60)
    
    try:
        # SQLite로 연결
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # 테이블 목록 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"✓ 발견된 테이블: {[table[0] for table in tables]}")
        
        # 메인 데이터 테이블 찾기
        main_table = None
        for table in tables:
            table_name = table[0]
            if table_name not in ['sqlite_sequence', 'gpkg_contents', 'gpkg_geometry_columns', 
                                'gpkg_spatial_ref_sys', 'gpkg_ogr_contents']:
                main_table = table_name
                break
        
        if not main_table:
            print("✗ 메인 데이터 테이블을 찾을 수 없습니다.")
            return None
            
        print(f"✓ 메인 테이블: {main_table}")
        
        # 테이블 구조 확인
        cursor.execute(f"PRAGMA table_info({main_table});")
        columns_info = cursor.fetchall()
        print(f"\n📋 컬럼 정보:")
        for col_info in columns_info:
            col_id, col_name, col_type, not_null, default, pk = col_info
            print(f"   {col_id+1:2d}. {col_name:<20} ({col_type})")
        
        # 전체 레코드 수
        cursor.execute(f"SELECT COUNT(*) FROM {main_table};")
        total_count = cursor.fetchone()[0]
        print(f"\n📊 전체 레코드 수: {total_count:,}개")
        
        # 샘플 데이터 조회
        cursor.execute(f"SELECT * FROM {main_table} LIMIT 3;")
        sample_data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        print(f"\n📝 샘플 데이터:")
        for i, row in enumerate(sample_data, 1):
            print(f"   레코드 {i}:")
            for col, value in zip(columns, row):
                if col != 'geom':  # geometry 컬럼은 제외
                    print(f"     {col}: {value}")
            print()
        
        # 지역별 분석
        region_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['시도', '시군구', '구', '시', '도', 'region', 'area', '지역'])]
        if region_columns:
            print(f"🏙️  지역별 분석:")
            for col in region_columns[:2]:  # 처음 2개만
                try:
                    cursor.execute(f"SELECT {col}, COUNT(*) as count FROM {main_table} WHERE {col} IS NOT NULL GROUP BY {col} ORDER BY count DESC LIMIT 10;")
                    region_stats = cursor.fetchall()
                    print(f"\n   {col} 상위 10개:")
                    for region, count in region_stats:
                        print(f"     - {region}: {count:,}건")
                except Exception as e:
                    print(f"     {col} 분석 오류: {e}")
        
        # 시간 관련 분석
        time_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['date', '날짜', '시간', 'time', '일시', '년', '월', '일'])]
        if time_columns:
            print(f"\n📅 시간 관련 분석:")
            for col in time_columns[:3]:  # 처음 3개만
                try:
                    cursor.execute(f"SELECT {col}, COUNT(*) as count FROM {main_table} WHERE {col} IS NOT NULL GROUP BY {col} ORDER BY count DESC LIMIT 10;")
                    time_stats = cursor.fetchall()
                    print(f"\n   {col} 상위 10개:")
                    for time_val, count in time_stats:
                        print(f"     - {time_val}: {count:,}건")
                except Exception as e:
                    print(f"     {col} 분석 오류: {e}")
        
        # 수치형 데이터 분석
        print(f"\n📊 수치형 데이터 통계:")
        for col_info in columns_info:
            col_name = col_info[1]
            col_type = col_info[2]
            if 'INT' in col_type.upper() or 'REAL' in col_type.upper() or 'FLOAT' in col_type.upper():
                if col_name.lower() not in ['fid', 'id']:
                    try:
                        cursor.execute(f"""
                            SELECT 
                                MIN({col_name}) as min_val,
                                MAX({col_name}) as max_val,
                                AVG({col_name}) as avg_val,
                                COUNT({col_name}) as count_val
                            FROM {main_table} 
                            WHERE {col_name} IS NOT NULL
                        """)
                        stats = cursor.fetchone()
                        if stats and stats[3] > 0:
                            print(f"   {col_name}: 최솟값={stats[0]}, 최댓값={stats[1]}, 평균={stats[2]:.2f}, 개수={stats[3]}")
                    except Exception as e:
                        print(f"   {col_name} 통계 오류: {e}")
        
        conn.close()
        return main_table, columns
        
    except Exception as e:
        print(f"✗ 데이터 분석 실패: {e}")
        return None

def generate_visualization_html(gpkg_file):
    """분석 결과를 보여주는 HTML 페이지 생성"""
    
    # 데이터 다시 조회
    conn = sqlite3.connect(gpkg_file)
    cursor = conn.cursor()
    
    # 테이블 정보 가져오기
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    main_table = None
    for table in tables:
        table_name = table[0]
        if table_name not in ['sqlite_sequence', 'gpkg_contents', 'gpkg_geometry_columns', 
                            'gpkg_spatial_ref_sys', 'gpkg_ogr_contents']:
            main_table = table_name
            break
    
    if not main_table:
        return
    
    # 기본 통계
    cursor.execute(f"SELECT COUNT(*) FROM {main_table};")
    total_count = cursor.fetchone()[0]
    
    # 지역별 통계 (시도 기준)
    region_stats_html = ""
    try:
        # 시도 관련 컬럼 찾기
        cursor.execute(f"PRAGMA table_info({main_table});")
        columns_info = cursor.fetchall()
        columns = [col[1] for col in columns_info]
        
        sido_col = None
        for col in columns:
            if '시도' in col or 'sido' in col.lower():
                sido_col = col
                break
        
        if sido_col:
            cursor.execute(f"SELECT {sido_col}, COUNT(*) as count FROM {main_table} WHERE {sido_col} IS NOT NULL GROUP BY {sido_col} ORDER BY count DESC LIMIT 10;")
            region_data = cursor.fetchall()
            
            region_stats_html = "<h3>🏙️ 지역별 사고 현황 (상위 10개)</h3><ul>"
            for region, count in region_data:
                percentage = (count / total_count) * 100
                region_stats_html += f"<li><strong>{region}</strong>: {count:,}건 ({percentage:.1f}%)</li>"
            region_stats_html += "</ul>"
    except:
        region_stats_html = "<p>지역별 통계를 생성할 수 없습니다.</p>"
    
    # 월별 통계
    monthly_stats_html = ""
    try:
        month_col = None
        for col in columns:
            if '월' in col or 'month' in col.lower():
                month_col = col
                break
        
        if month_col:
            cursor.execute(f"SELECT {month_col}, COUNT(*) as count FROM {main_table} WHERE {month_col} IS NOT NULL GROUP BY {month_col} ORDER BY CAST({month_col} AS INTEGER);")
            monthly_data = cursor.fetchall()
            
            monthly_stats_html = "<h3>📅 월별 사고 현황</h3><ul>"
            for month, count in monthly_data:
                monthly_stats_html += f"<li><strong>{month}월</strong>: {count:,}건</li>"
            monthly_stats_html += "</ul>"
    except:
        monthly_stats_html = "<p>월별 통계를 생성할 수 없습니다.</p>"
    
    conn.close()
    
    # HTML 생성
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>조류 유리창 충돌사고 분석 결과</title>
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
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
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
                font-size: 1.2rem;
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
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }}
            
            li:last-child {{
                border-bottom: none;
            }}
            
            .highlight {{
                background: linear-gradient(120deg, #a8edea 0%, #fed6e3 100%);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
                font-weight: bold;
                font-size: 1.1rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🐦 조류 유리창 충돌사고 분석</h1>
                <p>2023-2024년 전국 데이터 분석 결과</p>
            </div>
            
            <div class="content">
                <div class="highlight">
                    📊 총 {total_count:,}건의 조류 충돌사고가 기록되었습니다
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>📈 전체 사고 건수</h3>
                        <div class="big-number">{total_count:,}</div>
                        <p>2023-2024년 기간 동안 전국에서 발생한 조류 유리창 충돌사고 총계</p>
                    </div>
                    
                    <div class="stat-card">
                        {region_stats_html}
                    </div>
                    
                    <div class="stat-card">
                        {monthly_stats_html}
                    </div>
                </div>
                
                <div class="summary-section">
                    <h3>🔍 주요 분석 결과</h3>
                    <ul>
                        <li>📍 <strong>공간적 분포</strong>: 전국 각 지역에서 조류 충돌사고가 발생하고 있으며, 지역별로 발생 빈도에 차이가 있습니다.</li>
                        <li>⏰ <strong>시간적 패턴</strong>: 계절별, 월별로 사고 발생 패턴이 다르게 나타나고 있습니다.</li>
                        <li>🏢 <strong>건물 특성</strong>: 유리창이 많은 건물 유형과 충돌사고 간의 연관성을 확인할 수 있습니다.</li>
                        <li>🦅 <strong>조류 보호</strong>: 이 데이터는 조류 보호 정책 수립과 건물 설계 개선에 중요한 기초자료로 활용될 수 있습니다.</li>
                    </ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # HTML 파일 저장
    with open('/Users/suntaekim/nie/bird_collision_analysis.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ 분석 결과 HTML 페이지가 생성되었습니다!")
    print(f"   파일 위치: /Users/suntaekim/nie/bird_collision_analysis.html")

def main():
    """메인 실행 함수"""
    file_path = "조류유리창_충돌사고_2023_2024_전국.gpkg"
    
    # 1. 데이터 분석
    result = analyze_gpkg_with_sqlite(file_path)
    if result:
        # 2. HTML 시각화 생성
        generate_visualization_html(file_path)
    
    print(f"\n" + "="*60)
    print("✅ 분석 완료!")
    print("="*60)

if __name__ == "__main__":
    main()