-- SQLite MCP 테스트 쿼리: 버드세이버 효과 분석
-- 생성일: 2025-09-29 15:43:42


            SELECT 
                bird_saver,
                COUNT(*) as incidents,
                COUNT(DISTINCT korean_name) as species_count,
                AVG(individual_count) as avg_individuals,
                COUNT(DISTINCT province) as provinces
            FROM bird_collisions
            WHERE bird_saver IN ('Y', 'N')
            GROUP BY bird_saver;
            