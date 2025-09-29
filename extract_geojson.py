#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
조류 충돌사고 데이터를 GeoJSON으로 추출
"""

import sqlite3
import json
import random

def extract_bird_data_to_geojson(file_path, sample_size=1000):
    """조류 충돌사고 데이터를 GeoJSON으로 추출"""
    print("=" * 60)
    print("조류 충돌사고 데이터 GeoJSON 추출")
    print("=" * 60)
    
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    
    # 데이터 테이블에서 위치 정보와 상세 정보 추출
    table_name = "조류유리창_충돌사고_2023_2024_전국"
    
    # 전체 데이터 수 확인
    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
    total_count = cursor.fetchone()[0]
    print(f"전체 데이터: {total_count:,}개")
    
    # 샘플링을 위한 랜덤 시드 설정
    random.seed(42)
    
    # 데이터 추출 (샘플링)
    if total_count > sample_size:
        print(f"성능을 위해 {sample_size:,}개 샘플 추출")
        # 랜덤 샘플링
        cursor.execute(f"""
            SELECT 위도, 경도, 한글보통명, 철새유형명, 시설물유형명, 관찰일자, 시도명, 서식지유형명, 개체수
            FROM `{table_name}` 
            WHERE 위도 IS NOT NULL AND 경도 IS NOT NULL 
            AND 위도 != '' AND 경도 != ''
            ORDER BY RANDOM() 
            LIMIT {sample_size}
        """)
    else:
        cursor.execute(f"""
            SELECT 위도, 경도, 한글보통명, 철새유형명, 시설물유형명, 관찰일자, 시도명, 서식지유형명, 개체수
            FROM `{table_name}` 
            WHERE 위도 IS NOT NULL AND 경도 IS NOT NULL 
            AND 위도 != '' AND 경도 != ''
        """)
    
    data = cursor.fetchall()
    print(f"추출된 데이터: {len(data):,}개")
    
    # GeoJSON 구조 생성
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    
    valid_count = 0
    for row in data:
        try:
            lat, lon, species, migratory_type, facility_type, observation_date, sido, habitat_type, count = row
            
            # 좌표 유효성 검사
            lat_float = float(lat)
            lon_float = float(lon)
            
            # 한국 내 좌표인지 확인 (대략적 범위)
            if 33.0 <= lat_float <= 43.0 and 124.0 <= lon_float <= 132.0:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon_float, lat_float]
                    },
                    "properties": {
                        "species": species or "미확인",
                        "migratory_type": migratory_type or "미분류",
                        "facility_type": facility_type or "미분류",
                        "observation_date": observation_date or "",
                        "sido": sido or "미분류",
                        "habitat_type": habitat_type or "미분류",
                        "count": count or "1"
                    }
                }
                geojson["features"].append(feature)
                valid_count += 1
        except (ValueError, TypeError):
            continue
    
    print(f"유효한 좌표 데이터: {valid_count:,}개")
    
    # GeoJSON 파일 저장
    with open('/Users/suntaekim/nie/bird_collision_data.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    
    print("✅ GeoJSON 파일 생성 완료: bird_collision_data.geojson")
    
    conn.close()
    return valid_count

def get_statistics_for_map(file_path):
    """지도용 통계 데이터 생성"""
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    
    table_name = "조류유리창_충돌사고_2023_2024_전국"
    
    # 시도별 통계
    cursor.execute(f"""
        SELECT 시도명, COUNT(*) as count 
        FROM `{table_name}` 
        WHERE 시도명 IS NOT NULL AND 시도명 != ''
        GROUP BY 시도명 
        ORDER BY count DESC
    """)
    sido_stats = cursor.fetchall()
    
    # 월별 통계
    cursor.execute(f"""
        SELECT strftime('%m', 관찰일자) as month, COUNT(*) as count 
        FROM `{table_name}` 
        WHERE 관찰일자 IS NOT NULL AND 관찰일자 != ''
        GROUP BY month 
        ORDER BY month
    """)
    monthly_stats = cursor.fetchall()
    
    # 조류 종별 통계
    cursor.execute(f"""
        SELECT 한글보통명, COUNT(*) as count 
        FROM `{table_name}` 
        WHERE 한글보통명 IS NOT NULL AND 한글보통명 != '' AND 한글보통명 != '동정불가'
        GROUP BY 한글보통명 
        ORDER BY count DESC 
        LIMIT 10
    """)
    species_stats = cursor.fetchall()
    
    # 시설물 유형별 통계
    cursor.execute(f"""
        SELECT 시설물유형명, COUNT(*) as count 
        FROM `{table_name}` 
        WHERE 시설물유형명 IS NOT NULL AND 시설물유형명 != ''
        GROUP BY 시설물유형명 
        ORDER BY count DESC
    """)
    facility_stats = cursor.fetchall()
    
    conn.close()
    
    # 통계 데이터를 JSON으로 저장
    stats_data = {
        "sido_stats": [{"name": name, "count": count} for name, count in sido_stats],
        "monthly_stats": [{"month": month, "count": count} for month, count in monthly_stats if month],
        "species_stats": [{"name": name, "count": count} for name, count in species_stats],
        "facility_stats": [{"name": name, "count": count} for name, count in facility_stats]
    }
    
    with open('/Users/suntaekim/nie/bird_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, ensure_ascii=False, indent=2)
    
    print("✅ 통계 데이터 JSON 파일 생성 완료: bird_statistics.json")
    return stats_data

def main():
    file_path = "조류유리창_충돌사고_2023_2024_전국.gpkg"
    
    # 1. GeoJSON 데이터 추출
    valid_count = extract_bird_data_to_geojson(file_path, sample_size=2000)
    
    # 2. 통계 데이터 생성
    stats = get_statistics_for_map(file_path)
    
    print(f"\n" + "=" * 60)
    print("✅ 데이터 추출 완료!")
    print(f"   - GeoJSON: {valid_count:,}개 지점")
    print(f"   - 시도별 통계: {len(stats['sido_stats'])}개")
    print(f"   - 조류 종 통계: {len(stats['species_stats'])}개")
    print("=" * 60)

if __name__ == "__main__":
    main()