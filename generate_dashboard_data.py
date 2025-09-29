#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대시보드용 샘플 데이터 생성
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
import random

def generate_dashboard_data():
    """대시보드용 데이터 생성"""
    try:
        # 실제 데이터베이스에서 샘플 데이터 추출
        conn = sqlite3.connect('조류유리창_충돌사고_2023_2024_전국.gpkg')
        
        # 2023년과 2024년 데이터를 균등하게 가져오기
        query = """
        SELECT 
            시도명, 한글보통명, 개체수,
            위도, 경도, 관찰일자, 시설물유형명,
            버드세이버여부, 철새유형명
        FROM 조류유리창_충돌사고_2023_2024_전국 
        WHERE (관찰일자 LIKE '2023%' AND ROWID % 20 = 0) 
           OR (관찰일자 LIKE '2024%' AND ROWID % 15 = 0)
        LIMIT 1000
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # DataFrame을 dict 리스트로 변환
        data = df.to_dict('records')
        
        # 날짜 형식 변환
        for item in data:
            if item['관찰일자']:
                try:
                    # 날짜가 문자열인 경우 파싱
                    if isinstance(item['관찰일자'], str):
                        item['관찰일자'] = pd.to_datetime(item['관찰일자']).strftime('%Y-%m-%d')
                except:
                    # 파싱 실패시 기본 날짜 사용
                    item['관찰일자'] = '2023-06-15'
        
        # JSON 파일로 저장
        output = {
            'raw_data': data,
            'generated_at': datetime.now().isoformat(),
            'total_records': len(data)
        }
        
        with open('bird_analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 대시보드 데이터 생성 완료: {len(data)}개 레코드")
        return True
        
    except Exception as e:
        print(f"❌ 실제 데이터 로드 실패: {e}")
        print("시뮬레이션 데이터를 생성합니다...")
        
        # 시뮬레이션 데이터 생성
        regions = ['서울특별시', '경기도', '인천광역시', '부산광역시', '대구광역시', 
                  '광주광역시', '대전광역시', '울산광역시', '강원도', '충청북도', 
                  '충청남도', '전라북도', '전라남도', '경상북도', '경상남도', 
                  '제주특별자치도', '세종특별자치시']
        
        species = ['멧비둘기', '직박구리', '참새', '물까치', '박새', '되지빠귀', 
                  '집비둘기', '붉은머리오목눈이', '흰배지빠귀', '물총새']
        
        facilities = ['방음벽', '건물', '기타']
        
        data = []
        
        for i in range(1000):
            # 2023-2024년 랜덤 날짜 생성 (2024년에 더 많은 가중치)
            if random.random() < 0.6:  # 60%는 2024년
                year = 2024
                month = random.randint(1, 12)
                day = random.randint(1, 28)
            else:  # 40%는 2023년
                year = 2023
                month = random.randint(1, 12)
                day = random.randint(1, 28)
            
            random_date = datetime(year, month, day)
            
            data.append({
                '관찰일자': random_date.strftime('%Y-%m-%d'),
                '시도명': random.choice(regions),
                '한글보통명': random.choice(species),
                '시설물유형명': random.choice(facilities),
                '개체수': random.randint(1, 5),
                '위도': 36.5 + (random.random() - 0.5) * 4,
                '경도': 127.8 + (random.random() - 0.5) * 6,
                '버드세이버여부': random.choice(['Y', 'N']),
                '철새유형명': random.choice(['텃새', '여름철새', '겨울철새', '나그네새'])
            })
        
        output = {
            'raw_data': data,
            'generated_at': datetime.now().isoformat(),
            'total_records': len(data),
            'data_type': 'simulation'
        }
        
        with open('bird_analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 시뮬레이션 데이터 생성 완료: {len(data)}개 레코드")
        return True

if __name__ == "__main__":
    generate_dashboard_data()