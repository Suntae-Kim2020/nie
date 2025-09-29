-- SQLite MCP 테스트 쿼리: 기본 통계 조회
-- 생성일: 2025-09-29 15:43:42


            SELECT 
                COUNT(*) as total_incidents,
                COUNT(DISTINCT korean_name) as species_count,
                COUNT(DISTINCT province) as province_count,
                SUM(individual_count) as total_individuals,
                MIN(observation_date) as first_date,
                MAX(observation_date) as latest_date
            FROM bird_collisions;
            