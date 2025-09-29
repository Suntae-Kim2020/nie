-- SQLite MCP 테스트 쿼리: 지리적 핫스팟 분석
-- 생성일: 2025-09-29 15:43:42


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
            