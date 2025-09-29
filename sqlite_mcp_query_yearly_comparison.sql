-- SQLite MCP 테스트 쿼리: 연도별 비교 분석
-- 생성일: 2025-09-29 15:43:42


            SELECT 
                survey_year,
                COUNT(*) as incidents,
                COUNT(DISTINCT korean_name) as species_count,
                COUNT(DISTINCT province) as affected_provinces,
                SUM(individual_count) as total_individuals
            FROM bird_collisions
            GROUP BY survey_year
            ORDER BY survey_year;
            