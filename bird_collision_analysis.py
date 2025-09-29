#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
조류 유리창 충돌사고 데이터 분석
2023-2024 전국 데이터 탐색 및 분석
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def load_and_explore_data(file_path):
    """GeoPackage 파일을 로드하고 기본 정보를 탐색"""
    print("=" * 60)
    print("조류 유리창 충돌사고 데이터 분석")
    print("=" * 60)
    
    # 데이터 로드
    try:
        gdf = gpd.read_file(file_path)
        print(f"✓ 데이터 로드 완료: {len(gdf)}개 레코드")
    except Exception as e:
        print(f"✗ 데이터 로드 실패: {e}")
        return None
    
    # 기본 정보 출력
    print(f"\n📊 데이터 기본 정보:")
    print(f"   - 전체 레코드 수: {len(gdf):,}개")
    print(f"   - 컬럼 수: {len(gdf.columns)}개")
    print(f"   - 좌표 시스템: {gdf.crs}")
    
    # 컬럼 정보
    print(f"\n📋 컬럼 목록:")
    for i, col in enumerate(gdf.columns, 1):
        dtype = str(gdf[col].dtype)
        null_count = gdf[col].isnull().sum()
        print(f"   {i:2d}. {col:<20} ({dtype:<10}) - 결측값: {null_count:,}개")
    
    # 샘플 데이터
    print(f"\n📝 샘플 데이터 (처음 3개 레코드):")
    print(gdf.head(3).to_string())
    
    return gdf

def analyze_spatial_distribution(gdf):
    """공간적 분포 분석"""
    print(f"\n🗺️  공간적 분포 분석:")
    
    # 좌표 범위
    if 'geometry' in gdf.columns:
        bounds = gdf.total_bounds
        print(f"   - 경도 범위: {bounds[0]:.6f} ~ {bounds[2]:.6f}")
        print(f"   - 위도 범위: {bounds[1]:.6f} ~ {bounds[3]:.6f}")
        
        # 중심점
        centroid = gdf.geometry.centroid
        center_lon = centroid.x.mean()
        center_lat = centroid.y.mean()
        print(f"   - 중심점: 경도 {center_lon:.6f}, 위도 {center_lat:.6f}")

def analyze_temporal_patterns(gdf):
    """시간별/계절별 패턴 분석"""
    print(f"\n📅 시간별/계절별 패턴 분석:")
    
    # 날짜/시간 컬럼 찾기
    date_columns = []
    for col in gdf.columns:
        if any(keyword in col.lower() for keyword in ['date', '날짜', '시간', 'time', '일시']):
            date_columns.append(col)
    
    print(f"   - 발견된 시간 관련 컬럼: {date_columns}")
    
    if date_columns:
        for col in date_columns:
            print(f"\n   📅 {col} 컬럼 분석:")
            # 데이터 타입 확인
            print(f"      - 데이터 타입: {gdf[col].dtype}")
            print(f"      - 고유값 개수: {gdf[col].nunique()}")
            print(f"      - 결측값: {gdf[col].isnull().sum()}개")
            
            # 샘플 값들
            sample_values = gdf[col].dropna().head(5).tolist()
            print(f"      - 샘플 값: {sample_values}")

def analyze_regional_statistics(gdf):
    """지역별 통계 분석"""
    print(f"\n🏙️  지역별 통계 분석:")
    
    # 지역 관련 컬럼 찾기
    region_columns = []
    for col in gdf.columns:
        if any(keyword in col.lower() for keyword in ['시도', '시군구', '구', '시', '도', 'region', 'area', '지역', '행정']):
            region_columns.append(col)
    
    print(f"   - 발견된 지역 관련 컬럼: {region_columns}")
    
    for col in region_columns:
        if col in gdf.columns:
            print(f"\n   🏘️  {col} 분석:")
            value_counts = gdf[col].value_counts().head(10)
            print(f"      상위 10개 지역:")
            for region, count in value_counts.items():
                print(f"        - {region}: {count:,}건")

def analyze_additional_attributes(gdf):
    """추가 속성 분석"""
    print(f"\n🔍 추가 속성 분석:")
    
    # 수치형 컬럼 분석
    numeric_columns = gdf.select_dtypes(include=[np.number]).columns.tolist()
    if 'geometry' in numeric_columns:
        numeric_columns.remove('geometry')
    
    print(f"\n   📊 수치형 컬럼 통계:")
    for col in numeric_columns:
        stats = gdf[col].describe()
        print(f"      {col}:")
        print(f"        - 평균: {stats['mean']:.2f}")
        print(f"        - 중앙값: {stats['50%']:.2f}")
        print(f"        - 최솟값: {stats['min']:.2f}")
        print(f"        - 최댓값: {stats['max']:.2f}")
    
    # 범주형 컬럼 분석
    categorical_columns = gdf.select_dtypes(include=['object']).columns.tolist()
    if 'geometry' in categorical_columns:
        categorical_columns.remove('geometry')
    
    print(f"\n   📋 범주형 컬럼 분석:")
    for col in categorical_columns[:5]:  # 처음 5개만
        unique_count = gdf[col].nunique()
        print(f"      {col}: {unique_count}개 고유값")
        if unique_count <= 20:  # 고유값이 20개 이하인 경우만 상세 표시
            value_counts = gdf[col].value_counts().head(5)
            for value, count in value_counts.items():
                print(f"        - {value}: {count}건")

def generate_summary_report(gdf):
    """요약 보고서 생성"""
    print(f"\n" + "="*60)
    print("📈 분석 요약 보고서")
    print("="*60)
    
    total_records = len(gdf)
    print(f"🔹 전체 사고 건수: {total_records:,}건")
    
    # 시도별 통계 (만약 해당 컬럼이 있다면)
    region_cols = [col for col in gdf.columns if any(keyword in col.lower() for keyword in ['시도', 'sido'])]
    if region_cols:
        region_col = region_cols[0]
        region_stats = gdf[region_col].value_counts()
        print(f"🔹 지역별 사고 현황 (상위 5개):")
        for i, (region, count) in enumerate(region_stats.head(5).items(), 1):
            percentage = (count / total_records) * 100
            print(f"   {i}. {region}: {count:,}건 ({percentage:.1f}%)")
    
    # 연도별 통계 (만약 날짜 컬럼이 있다면)
    date_cols = [col for col in gdf.columns if any(keyword in col.lower() for keyword in ['date', '날짜', '년'])]
    if date_cols:
        print(f"🔹 시간 관련 데이터: {len(date_cols)}개 컬럼")
    
    print(f"\n✅ 분석 완료!")

def main():
    """메인 실행 함수"""
    file_path = "조류유리창_충돌사고_2023_2024_전국.gpkg"
    
    # 1. 데이터 로드 및 기본 탐색
    gdf = load_and_explore_data(file_path)
    if gdf is None:
        return
    
    # 2. 공간적 분포 분석
    analyze_spatial_distribution(gdf)
    
    # 3. 시간별/계절별 패턴 분석
    analyze_temporal_patterns(gdf)
    
    # 4. 지역별 통계 분석
    analyze_regional_statistics(gdf)
    
    # 5. 추가 속성 분석
    analyze_additional_attributes(gdf)
    
    # 6. 요약 보고서
    generate_summary_report(gdf)
    
    return gdf

if __name__ == "__main__":
    # 분석 실행
    bird_data = main()