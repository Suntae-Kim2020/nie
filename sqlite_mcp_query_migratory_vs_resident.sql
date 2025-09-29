-- SQLite MCP 테스트 쿼리: 철새 vs 텃새 분석
-- 생성일: 2025-09-29 15:43:42


            SELECT 
                migratory_type,
                COUNT(*) as incidents,
                COUNT(DISTINCT korean_name) as species_count,
                SUM(individual_count) as total_individuals,
                COUNT(DISTINCT province) as affected_provinces
            FROM bird_collisions
            WHERE migratory_type IS NOT NULL
            GROUP BY migratory_type
            ORDER BY incidents DESC;
            