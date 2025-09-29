#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
조류 충돌사고 고급 통계 분석
건물 유형별, 조류 종별, 위험도 분석
"""

import sqlite3
import pandas as pd
import numpy as np
import json
from collections import Counter, defaultdict
import math
from datetime import datetime

def advanced_building_analysis(file_path):
    """건물 유형별 상세 사고 분석"""
    print("=" * 60)
    print("🏢 건물 유형별 사고 상세 분석")
    print("=" * 60)
    
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    table_name = "조류유리창_충돌사고_2023_2024_전국"
    
    # 1. 시설물 유형별 기본 통계
    cursor.execute(f"""
        SELECT 시설물유형명, COUNT(*) as total_accidents,
               COUNT(DISTINCT 시도명) as affected_regions,
               COUNT(DISTINCT 한글보통명) as affected_species
        FROM `{table_name}` 
        WHERE 시설물유형명 IS NOT NULL AND 시설물유형명 != ''
        GROUP BY 시설물유형명 
        ORDER BY total_accidents DESC
    """)
    
    facility_stats = cursor.fetchall()
    
    print("📊 시설물 유형별 기본 통계:")
    for facility, accidents, regions, species in facility_stats:
        print(f"   🏗️  {facility}:")
        print(f"      - 총 사고: {accidents:,}건")
        print(f"      - 영향 지역: {regions}개 시도")
        print(f"      - 영향 조류: {species}종")
        print(f"      - 전체 대비: {(accidents/15118)*100:.1f}%")
        print()
    
    # 2. 시설물별 지역 분포
    print("🗺️  시설물별 지역 분포 분석:")
    for facility, _, _, _ in facility_stats:
        cursor.execute(f"""
            SELECT 시도명, COUNT(*) as count
            FROM `{table_name}` 
            WHERE 시설물유형명 = ? AND 시도명 IS NOT NULL
            GROUP BY 시도명 
            ORDER BY count DESC 
            LIMIT 5
        """, (facility,))
        
        region_data = cursor.fetchall()
        print(f"\n   📍 {facility} 상위 5개 지역:")
        for region, count in region_data:
            print(f"      - {region}: {count:,}건")
    
    # 3. 시설물별 조류 피해 분석
    print("\n🐦 시설물별 조류 피해 분석:")
    facility_species_analysis = {}
    
    for facility, _, _, _ in facility_stats:
        cursor.execute(f"""
            SELECT 한글보통명, COUNT(*) as count
            FROM `{table_name}` 
            WHERE 시설물유형명 = ? AND 한글보통명 IS NOT NULL AND 한글보통명 != '동정불가'
            GROUP BY 한글보통명 
            ORDER BY count DESC 
            LIMIT 5
        """, (facility,))
        
        species_data = cursor.fetchall()
        facility_species_analysis[facility] = species_data
        
        print(f"\n   🦅 {facility} 주요 피해 조류:")
        for species, count in species_data:
            print(f"      - {species}: {count:,}건")
    
    # 4. 시설물별 계절성 분석
    print("\n📅 시설물별 계절성 분석:")
    for facility, _, _, _ in facility_stats[:3]:  # 상위 3개만
        cursor.execute(f"""
            SELECT 
                CASE 
                    WHEN CAST(strftime('%m', 관찰일자) AS INTEGER) IN (3,4,5) THEN '봄'
                    WHEN CAST(strftime('%m', 관찰일자) AS INTEGER) IN (6,7,8) THEN '여름'
                    WHEN CAST(strftime('%m', 관찰일자) AS INTEGER) IN (9,10,11) THEN '가을'
                    WHEN CAST(strftime('%m', 관찰일자) AS INTEGER) IN (12,1,2) THEN '겨울'
                    ELSE '미분류'
                END as season,
                COUNT(*) as count
            FROM `{table_name}` 
            WHERE 시설물유형명 = ? AND 관찰일자 IS NOT NULL
            GROUP BY season 
            ORDER BY count DESC
        """, (facility,))
        
        seasonal_data = cursor.fetchall()
        print(f"\n   🌱 {facility} 계절별 사고:")
        for season, count in seasonal_data:
            if season != '미분류':
                print(f"      - {season}: {count:,}건")
    
    conn.close()
    return facility_stats, facility_species_analysis

def species_risk_analysis(file_path):
    """조류 종별 충돌 위험도 분석"""
    print("\n" + "=" * 60)
    print("🐦 조류 종별 충돌 위험도 분석")
    print("=" * 60)
    
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    table_name = "조류유리창_충돌사고_2023_2024_전국"
    
    # 1. 조류 종별 기본 통계
    cursor.execute(f"""
        SELECT 한글보통명, 철새유형명, COUNT(*) as accident_count,
               COUNT(DISTINCT 시도명) as regions,
               COUNT(DISTINCT 시설물유형명) as facility_types
        FROM `{table_name}` 
        WHERE 한글보통명 IS NOT NULL AND 한글보통명 != '' AND 한글보통명 != '동정불가'
        GROUP BY 한글보통명, 철새유형명
        ORDER BY accident_count DESC 
        LIMIT 20
    """)
    
    species_stats = cursor.fetchall()
    
    print("📊 조류 종별 위험도 순위 (상위 20종):")
    print(f"{'순위':<4} {'조류명':<15} {'철새유형':<10} {'사고건수':<8} {'영향지역':<6} {'시설물종류':<8} {'위험도점수':<8}")
    print("-" * 70)
    
    species_risk_scores = []
    for i, (species, migratory_type, accidents, regions, facilities) in enumerate(species_stats, 1):
        # 위험도 점수 계산: 사고건수 + 지역분포 + 시설물다양성
        risk_score = accidents + (regions * 10) + (facilities * 5)
        species_risk_scores.append((species, migratory_type, accidents, regions, facilities, risk_score))
        
        print(f"{i:<4} {species:<15} {migratory_type or '미분류':<10} {accidents:<8} {regions:<6} {facilities:<8} {risk_score:<8}")
    
    # 2. 철새 유형별 위험도 분석
    print(f"\n🦅 철새 유형별 위험도 분석:")
    cursor.execute(f"""
        SELECT 철새유형명, COUNT(*) as total_accidents,
               COUNT(DISTINCT 한글보통명) as species_count,
               AVG(CAST(개체수 AS FLOAT)) as avg_individuals
        FROM `{table_name}` 
        WHERE 철새유형명 IS NOT NULL AND 철새유형명 != ''
        GROUP BY 철새유형명 
        ORDER BY total_accidents DESC
    """)
    
    migratory_stats = cursor.fetchall()
    for migratory_type, accidents, species_count, avg_individuals in migratory_stats:
        print(f"   🔸 {migratory_type}:")
        print(f"      - 총 사고: {accidents:,}건")
        print(f"      - 영향받은 종: {species_count}종")
        print(f"      - 평균 개체수: {avg_individuals:.1f}마리")
        print(f"      - 종당 평균 사고: {accidents/species_count:.1f}건")
    
    # 3. 고위험 조류의 시설물별 선호도
    print(f"\n🎯 고위험 조류의 시설물별 선호도:")
    high_risk_species = [species[0] for species in species_risk_scores[:5]]
    
    for species in high_risk_species:
        cursor.execute(f"""
            SELECT 시설물유형명, COUNT(*) as count
            FROM `{table_name}` 
            WHERE 한글보통명 = ? AND 시설물유형명 IS NOT NULL
            GROUP BY 시설물유형명 
            ORDER BY count DESC
        """, (species,))
        
        facility_preference = cursor.fetchall()
        total_accidents = sum(count for _, count in facility_preference)
        
        print(f"\n   🦅 {species} (총 {total_accidents}건):")
        for facility, count in facility_preference:
            percentage = (count / total_accidents) * 100
            print(f"      - {facility}: {count}건 ({percentage:.1f}%)")
    
    conn.close()
    return species_risk_scores, migratory_stats

def building_risk_factor_analysis(file_path):
    """건물 유형별 위험 요소 분석"""
    print("\n" + "=" * 60)
    print("⚠️  건물 유형별 위험 요소 분석")
    print("=" * 60)
    
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()
    table_name = "조류유리창_충돌사고_2023_2024_전국"
    
    # 1. 시설물별 버드세이버 설치 현황
    cursor.execute(f"""
        SELECT 시설물유형명, 버드세이버여부,
               COUNT(*) as count
        FROM `{table_name}` 
        WHERE 시설물유형명 IS NOT NULL AND 버드세이버여부 IS NOT NULL
        GROUP BY 시설물유형명, 버드세이버여부
        ORDER BY 시설물유형명, count DESC
    """)
    
    bird_saver_stats = cursor.fetchall()
    
    print("🛡️  시설물별 버드세이버 설치 현황:")
    facility_bird_saver = defaultdict(dict)
    for facility, bird_saver, count in bird_saver_stats:
        facility_bird_saver[facility][bird_saver] = count
    
    for facility, stats in facility_bird_saver.items():
        total = sum(stats.values())
        print(f"\n   🏗️  {facility} (총 {total:,}건):")
        for status, count in stats.items():
            percentage = (count / total) * 100
            status_text = "설치됨" if status == 'Y' else "미설치" if status == 'N' else "정보없음"
            print(f"      - 버드세이버 {status_text}: {count:,}건 ({percentage:.1f}%)")
    
    # 2. 서식지 유형별 위험도 분석
    print(f"\n🌳 서식지 유형별 위험도 분석:")
    cursor.execute(f"""
        SELECT 서식지유형명, 시설물유형명, COUNT(*) as count
        FROM `{table_name}` 
        WHERE 서식지유형명 IS NOT NULL AND 시설물유형명 IS NOT NULL
        GROUP BY 서식지유형명, 시설물유형명
        ORDER BY 서식지유형명, count DESC
    """)
    
    habitat_facility_stats = cursor.fetchall()
    habitat_analysis = defaultdict(list)
    
    for habitat, facility, count in habitat_facility_stats:
        habitat_analysis[habitat].append((facility, count))
    
    for habitat, facilities in habitat_analysis.items():
        total = sum(count for _, count in facilities)
        print(f"\n   🌿 {habitat} (총 {total:,}건):")
        for facility, count in facilities[:3]:  # 상위 3개만
            percentage = (count / total) * 100
            print(f"      - {facility}: {count:,}건 ({percentage:.1f}%)")
    
    # 3. 위험도 지수 계산
    print(f"\n📊 시설물별 종합 위험도 지수:")
    
    risk_factors = {}
    for facility, _, _, _ in [(f, 0, 0, 0) for f in ['방음벽', '건물', '기타']]:
        # 사고 빈도
        cursor.execute(f"""
            SELECT COUNT(*) FROM `{table_name}` 
            WHERE 시설물유형명 = ?
        """, (facility,))
        accident_freq = cursor.fetchone()[0]
        
        # 지역 분산도
        cursor.execute(f"""
            SELECT COUNT(DISTINCT 시도명) FROM `{table_name}` 
            WHERE 시설물유형명 = ?
        """, (facility,))
        region_spread = cursor.fetchone()[0]
        
        # 조류 다양성
        cursor.execute(f"""
            SELECT COUNT(DISTINCT 한글보통명) FROM `{table_name}` 
            WHERE 시설물유형명 = ? AND 한글보통명 != '동정불가'
        """, (facility,))
        species_diversity = cursor.fetchone()[0]
        
        # 버드세이버 미설치율
        cursor.execute(f"""
            SELECT 
                COUNT(CASE WHEN 버드세이버여부 = 'N' THEN 1 END) * 100.0 / COUNT(*) as no_bird_saver_rate
            FROM `{table_name}` 
            WHERE 시설물유형명 = ? AND 버드세이버여부 IN ('Y', 'N')
        """, (facility,))
        no_bird_saver_rate = cursor.fetchone()[0] or 0
        
        # 종합 위험도 지수 계산 (정규화)
        risk_index = (
            (accident_freq / 15118) * 40 +  # 사고빈도 40%
            (region_spread / 17) * 20 +     # 지역분산 20%
            (species_diversity / 200) * 20 + # 종다양성 20%
            (no_bird_saver_rate / 100) * 20  # 버드세이버미설치 20%
        ) * 100
        
        risk_factors[facility] = {
            'accident_freq': accident_freq,
            'region_spread': region_spread,
            'species_diversity': species_diversity,
            'no_bird_saver_rate': no_bird_saver_rate,
            'risk_index': risk_index
        }
        
        print(f"\n   ⚠️  {facility}:")
        print(f"      - 사고 빈도: {accident_freq:,}건")
        print(f"      - 지역 분산도: {region_spread}개 시도")
        print(f"      - 조류 다양성: {species_diversity}종")
        print(f"      - 버드세이버 미설치율: {no_bird_saver_rate:.1f}%")
        print(f"      - 🔥 종합 위험도 지수: {risk_index:.1f}/100")
    
    conn.close()
    return risk_factors

def generate_advanced_analysis_report(file_path):
    """고급 분석 결과 종합 보고서 생성"""
    print("\n" + "=" * 60)
    print("📋 고급 분석 종합 보고서 생성")
    print("=" * 60)
    
    # 분석 실행
    facility_stats, facility_species = advanced_building_analysis(file_path)
    species_risk_scores, migratory_stats = species_risk_analysis(file_path)
    risk_factors = building_risk_factor_analysis(file_path)
    
    # JSON 데이터 생성
    advanced_analysis_data = {
        "facility_analysis": {
            "basic_stats": [
                {
                    "facility": facility,
                    "accidents": accidents,
                    "regions": regions,
                    "species": species,
                    "percentage": round((accidents/15118)*100, 1)
                }
                for facility, accidents, regions, species in facility_stats
            ],
            "species_by_facility": {
                facility: [{"species": species, "count": count} for species, count in species_list]
                for facility, species_list in facility_species.items()
            }
        },
        "species_risk_analysis": {
            "high_risk_species": [
                {
                    "rank": i+1,
                    "species": species,
                    "migratory_type": migratory_type,
                    "accidents": accidents,
                    "regions": regions,
                    "facilities": facilities,
                    "risk_score": risk_score
                }
                for i, (species, migratory_type, accidents, regions, facilities, risk_score) in enumerate(species_risk_scores[:20])
            ],
            "migratory_type_stats": [
                {
                    "type": migratory_type,
                    "accidents": accidents,
                    "species_count": species_count,
                    "avg_individuals": round(avg_individuals or 0, 1)
                }
                for migratory_type, accidents, species_count, avg_individuals in migratory_stats
            ]
        },
        "risk_factors": risk_factors,
        "analysis_metadata": {
            "total_accidents": 15118,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "data_period": "2023-2024",
            "regions_covered": 17
        }
    }
    
    # JSON 파일 저장
    with open('/Users/suntaekim/nie/advanced_analysis_data.json', 'w', encoding='utf-8') as f:
        json.dump(advanced_analysis_data, f, ensure_ascii=False, indent=2)
    
    print("✅ 고급 분석 데이터 JSON 파일 생성: advanced_analysis_data.json")
    
    # 요약 출력
    print(f"\n📈 분석 요약:")
    print(f"   - 시설물 유형: {len(facility_stats)}개 분석")
    print(f"   - 고위험 조류: {len(species_risk_scores)}종 식별")
    print(f"   - 위험 요소: {len(risk_factors)}개 시설물 평가")
    print(f"   - 철새 유형: {len(migratory_stats)}개 카테고리")
    
    return advanced_analysis_data

def main():
    """메인 실행 함수"""
    file_path = "조류유리창_충돌사고_2023_2024_전국.gpkg"
    
    try:
        # 고급 통계 분석 실행
        analysis_data = generate_advanced_analysis_report(file_path)
        
        print(f"\n" + "="*60)
        print("🎉 고급 통계 분석 완료!")
        print("="*60)
        print("✅ 다음 분석이 완료되었습니다:")
        print("   1. 건물 유형별 사고 분석")
        print("   2. 조류 종별 충돌 위험도 분석") 
        print("   3. 건물 유형별 위험 요소 분석")
        print("   4. 종합 위험도 지수 계산")
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")

if __name__ == "__main__":
    main()