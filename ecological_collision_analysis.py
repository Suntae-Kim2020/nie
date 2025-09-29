#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Point
import folium
from folium.plugins import HeatMap
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = ['Arial Unicode MS', 'DejaVu Sans', 'sans-serif']

def load_ecological_data():
    """금강유역 생태지도 데이터 로드"""
    print("Loading F006 ecological shapefile...")
    try:
        eco_gdf = gpd.read_file('F006_20250118_30.shp', encoding='cp949')
        print(f"✓ Ecological data loaded: {len(eco_gdf)} features")
        print("Columns:", list(eco_gdf.columns))
        print("CRS:", eco_gdf.crs)
        return eco_gdf
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        try:
            eco_gdf = gpd.read_file('F006_20250118_30.shp', encoding='euc-kr')
            print(f"✓ Ecological data loaded with euc-kr: {len(eco_gdf)} features")
            return eco_gdf
        except Exception as e2:
            print(f"Error with euc-kr: {e2}")
            return None

def load_bird_collision_data():
    """조류충돌 데이터 로드"""
    print("\nLoading bird collision data...")
    try:
        bird_df = pd.read_csv('조류유리창_충돌사고_2023_2024_전국.csv', encoding='utf-8')
        print(f"✓ Bird collision data loaded: {len(bird_df)} records")
        
        # 위경도가 있는 데이터만 필터링
        bird_df = bird_df.dropna(subset=['위도', '경도'])
        print(f"✓ Records with coordinates: {len(bird_df)}")
        
        # GeoDataFrame으로 변환
        geometry = [Point(xy) for xy in zip(bird_df['경도'], bird_df['위도'])]
        bird_gdf = gpd.GeoDataFrame(bird_df, geometry=geometry, crs='EPSG:4326')
        
        return bird_gdf
    except Exception as e:
        print(f"Error loading bird data: {e}")
        return None

def analyze_spatial_intersection(eco_gdf, bird_gdf):
    """생태지도와 조류충돌 데이터의 공간교집합 분석"""
    print("\nPerforming spatial analysis...")
    
    # CRS 통일 (UTM-K 또는 적절한 투영좌표계)
    if eco_gdf.crs != bird_gdf.crs:
        if eco_gdf.crs is None:
            eco_gdf = eco_gdf.set_crs('EPSG:5179')  # UTM-K
        bird_gdf = bird_gdf.to_crs(eco_gdf.crs)
        print(f"✓ CRS unified to: {eco_gdf.crs}")
    
    # 공간조인 수행
    try:
        collision_in_eco = gpd.sjoin(bird_gdf, eco_gdf, how='inner', predicate='within')
        print(f"✓ Spatial join completed: {len(collision_in_eco)} collision points matched")
        return collision_in_eco
    except Exception as e:
        print(f"Error in spatial join: {e}")
        return None

def create_analysis_report(collision_in_eco, eco_gdf):
    """분석 결과 리포트 생성"""
    print("\nGenerating analysis report...")
    
    results = {}
    
    # 기본 통계
    results['total_collisions'] = len(collision_in_eco)
    results['ecological_features'] = len(eco_gdf)
    
    # 생태지도 컬럼별 분석 (주요 컬럼들 확인)
    eco_columns = eco_gdf.columns.tolist()
    print("Available ecological columns:", eco_columns)
    
    # 가능한 생태 분류 컬럼들 찾기
    analysis_columns = []
    for col in eco_columns:
        if any(keyword in col.lower() for keyword in ['생태', 'eco', 'type', 'class', '등급', 'grade']):
            analysis_columns.append(col)
    
    print(f"Analysis will focus on columns: {analysis_columns}")
    
    # 각 생태 분류별 충돌 건수 분석
    for col in analysis_columns[:3]:  # 최대 3개 컬럼만 분석
        if col in collision_in_eco.columns:
            try:
                collision_by_type = collision_in_eco.groupby(col).size().sort_values(ascending=False)
                results[f'collisions_by_{col}'] = collision_by_type.to_dict()
                print(f"✓ Analysis completed for {col}")
            except Exception as e:
                print(f"Error analyzing {col}: {e}")
    
    return results

def create_visualization_map(collision_in_eco, eco_gdf):
    """시각화 지도 생성"""
    print("\nCreating visualization map...")
    
    try:
        # 중심점 계산 (금강유역 중심으로)
        center_lat = collision_in_eco['위도'].mean()
        center_lon = collision_in_eco['경도'].mean()
        
        # Folium 지도 생성
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=9,
            tiles='OpenStreetMap'
        )
        
        # 조류충돌 지점 추가 (히트맵)
        heat_data = [[row['위도'], row['경도']] for idx, row in collision_in_eco.iterrows()]
        HeatMap(heat_data, radius=15, blur=10).add_to(m)
        
        # 개별 충돌 지점 마커 추가 (샘플링)
        sample_size = min(100, len(collision_in_eco))
        sample_data = collision_in_eco.sample(sample_size)
        
        for idx, row in sample_data.iterrows():
            folium.CircleMarker(
                location=[row['위도'], row['경도']],
                radius=3,
                popup=f"종: {row.get('조류종', 'Unknown')}<br>날짜: {row.get('관찰일자', 'Unknown')}",
                color='red',
                fill=True,
                fillOpacity=0.6
            ).add_to(m)
        
        # 지도 저장
        map_file = 'ecological_collision_analysis_map.html'
        m.save(map_file)
        print(f"✓ Map saved as {map_file}")
        
        return map_file
    except Exception as e:
        print(f"Error creating map: {e}")
        return None

def main():
    """메인 분석 실행"""
    print("=== 금강유역 생태지도 × 조류충돌 분석 ===")
    
    # 1. 데이터 로드
    eco_gdf = load_ecological_data()
    if eco_gdf is None:
        return
    
    bird_gdf = load_bird_collision_data()
    if bird_gdf is None:
        return
    
    # 2. 공간 교집합 분석
    collision_in_eco = analyze_spatial_intersection(eco_gdf, bird_gdf)
    if collision_in_eco is None:
        return
    
    # 3. 결과 분석
    results = create_analysis_report(collision_in_eco, eco_gdf)
    
    # 4. 시각화
    map_file = create_visualization_map(collision_in_eco, eco_gdf)
    
    # 5. 결과 출력
    print("\n=== 분석 결과 요약 ===")
    print(f"전체 충돌사고: {results['total_collisions']:,}건")
    print(f"생태지도 피처 수: {results['ecological_features']:,}개")
    
    # 주요 분석 결과 출력
    for key, value in results.items():
        if key.startswith('collisions_by_') and isinstance(value, dict):
            print(f"\n{key} 분석:")
            for category, count in list(value.items())[:5]:  # 상위 5개만 출력
                print(f"  {category}: {count}건")
    
    if map_file:
        print(f"\n✓ 시각화 지도: {map_file}")
    
    print("\n분석 완료!")

if __name__ == "__main__":
    main()