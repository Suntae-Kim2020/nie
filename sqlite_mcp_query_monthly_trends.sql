-- SQLite MCP 테스트 쿼리: 월별 사고 추이
-- 생성일: 2025-09-29 15:43:42


            SELECT 
                year,
                month,
                incidents,
                species_count,
                total_individuals
            FROM monthly_trends
            ORDER BY year, month;
            