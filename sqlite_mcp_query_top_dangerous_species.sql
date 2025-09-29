-- SQLite MCP 테스트 쿼리: 가장 위험한 조류 종 TOP 10
-- 생성일: 2025-09-29 15:43:42


            SELECT 
                korean_name,
                migratory_type,
                incident_count,
                total_individuals,
                affected_provinces
            FROM species_statistics
            LIMIT 10;
            