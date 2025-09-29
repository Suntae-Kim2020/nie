#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeoPackage 데이터를 CSV로 변환하여 MCP 테스트용으로 준비
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

def export_to_csv():
    """GeoPackage 데이터를 CSV로 내보내기"""
    try:
        print("🐦 조류 충돌 데이터 CSV 변환 시작...")
        
        # GeoPackage 파일 연결
        db_path = "조류유리창_충돌사고_2023_2024_전국.gpkg"
        if not os.path.exists(db_path):
            print(f"❌ 파일을 찾을 수 없습니다: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        
        # 전체 데이터 추출 쿼리
        query = """
        SELECT 
            fid,
            관찰번호,
            조사연도,
            관찰일자,
            등록일자,
            한글보통명 as 조류종,
            철새유형명 as 철새유형,
            서식지유형명 as 서식지유형,
            학명,
            영문보통명 as 영문명,
            한글계명 as 계,
            한글문명 as 문,
            한글강명 as 강,
            한글목명 as 목,
            한글과명 as 과,
            한글속명 as 속,
            종,
            위도,
            경도,
            개체수,
            시설물유형명 as 시설물유형,
            버드세이버여부,
            시도명 as 시도
        FROM 조류유리창_충돌사고_2023_2024_전국
        ORDER BY 관찰일자, 시도명
        """
        
        print("📊 데이터 추출 중...")
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # 데이터 정리
        print(f"✅ 데이터 추출 완료: {len(df):,}개 레코드")
        
        # 날짜 형식 정리
        df['관찰일자'] = pd.to_datetime(df['관찰일자'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['등록일자'] = pd.to_datetime(df['등록일자'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # 숫자 데이터 정리
        df['개체수'] = pd.to_numeric(df['개체수'], errors='coerce').fillna(1)
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce').round(6)
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce').round(6)
        
        # CSV 파일로 저장
        csv_filename = "조류유리창_충돌사고_2023_2024_전국.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        # 파일 정보 출력
        file_size = os.path.getsize(csv_filename) / (1024 * 1024)  # MB
        print(f"📁 CSV 파일 생성 완료:")
        print(f"   파일명: {csv_filename}")
        print(f"   크기: {file_size:.2f} MB")
        print(f"   레코드 수: {len(df):,}개")
        print(f"   컬럼 수: {len(df.columns)}개")
        
        # 데이터 요약 정보
        print("\n📋 데이터 요약:")
        print(f"   기간: {df['관찰일자'].min()} ~ {df['관찰일자'].max()}")
        print(f"   지역 수: {df['시도'].nunique()}개 시도")
        print(f"   조류 종 수: {df['조류종'].nunique()}개 종")
        print(f"   시설물 유형: {df['시설물유형'].nunique()}개 유형")
        
        # 상위 조류 종
        print(f"\n🐦 주요 조류 종 (상위 5개):")
        top_species = df['조류종'].value_counts().head(5)
        for species, count in top_species.items():
            print(f"   • {species}: {count:,}건")
        
        # 시설물별 분포
        print(f"\n🏗️ 시설물별 분포:")
        facility_counts = df['시설물유형'].value_counts()
        for facility, count in facility_counts.items():
            percentage = (count / len(df)) * 100
            print(f"   • {facility}: {count:,}건 ({percentage:.1f}%)")
        
        # MCP 테스트용 샘플 파일 생성
        sample_size = min(1000, len(df))
        sample_df = df.sample(n=sample_size, random_state=42)
        sample_filename = "조류충돌_샘플데이터_MCP테스트용.csv"
        sample_df.to_csv(sample_filename, index=False, encoding='utf-8-sig')
        
        print(f"\n🔬 MCP 테스트용 샘플 파일:")
        print(f"   파일명: {sample_filename}")
        print(f"   크기: {sample_size:,}개 레코드")
        print(f"   용도: ChatGPT MCP 기능 테스트")
        
        return True
        
    except Exception as e:
        print(f"❌ CSV 변환 중 오류 발생: {e}")
        return False

def create_data_dictionary():
    """데이터 딕셔너리 생성 (MCP 테스트 시 참고용)"""
    data_dict = {
        "파일명": "조류유리창_충돌사고_2023_2024_전국.csv",
        "설명": "2023-2024년 전국 조류 유리창 충돌 사고 데이터",
        "출처": "국립생물자원관",
        "컬럼_설명": {
            "fid": "고유 ID",
            "관찰번호": "관찰 기록 번호",
            "조사연도": "조사 년도 (2023, 2024)",
            "관찰일자": "사고 발생 일자 (YYYY-MM-DD)",
            "등록일자": "데이터 등록 일자",
            "조류종": "충돌한 조류의 한글명",
            "철새유형": "텃새/여름철새/겨울철새/나그네새",
            "서식지유형": "서식지 분류",
            "학명": "조류의 학명",
            "영문명": "조류의 영문명",
            "계": "생물 분류 - 계",
            "문": "생물 분류 - 문", 
            "강": "생물 분류 - 강",
            "목": "생물 분류 - 목",
            "과": "생물 분류 - 과",
            "속": "생물 분류 - 속",
            "종": "생물 분류 - 종",
            "위도": "사고 발생 위치 위도",
            "경도": "사고 발생 위치 경도",
            "개체수": "충돌한 개체 수",
            "시설물유형": "충돌 시설물 (방음벽/건물/기타)",
            "버드세이버여부": "조류 보호 장치 설치 여부 (Y/N)",
            "시도": "사고 발생 시도"
        },
        "분석_질의_예시": [
            "가장 많이 충돌하는 조류 종은?",
            "방음벽에서 가장 많이 발생하는 사고는 언제인가?",
            "지역별 사고 발생 패턴은?",
            "계절별 조류 충돌 빈도는?",
            "버드세이버 설치 효과는?",
            "텃새와 철새 중 어느 쪽이 더 많이 충돌하는가?",
            "월별 사고 추이 분석",
            "시설물 유형별 위험도 순위"
        ]
    }
    
    # JSON 파일로 저장
    import json
    with open("데이터_딕셔너리_MCP테스트용.json", "w", encoding="utf-8") as f:
        json.dump(data_dict, f, ensure_ascii=False, indent=2)
    
    print("📚 데이터 딕셔너리 생성 완료: 데이터_딕셔너리_MCP테스트용.json")

if __name__ == "__main__":
    print("🔧 MCP 테스트를 위한 CSV 데이터 준비")
    print("=" * 60)
    
    if export_to_csv():
        create_data_dictionary()
        print("\n✅ 모든 작업 완료!")
        print("\n📋 ChatGPT MCP 테스트 방법:")
        print("1. '조류유리창_충돌사고_2023_2024_전국.csv' 파일을 ChatGPT에 업로드")
        print("2. 또는 '조류충돌_샘플데이터_MCP테스트용.csv' 사용 (가벼운 버전)")
        print("3. '데이터_딕셔너리_MCP테스트용.json' 파일도 함께 업로드하면 더 좋음")
        print("4. 조류 충돌 데이터에 대한 다양한 질의 수행")
    else:
        print("\n❌ 작업 실패")