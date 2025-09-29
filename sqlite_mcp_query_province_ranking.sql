-- SQLite MCP 테스트 쿼리: 지역별 사고 순위
-- 생성일: 2025-09-29 15:43:42


            SELECT 
                province,
                total_incidents,
                species_count,
                total_individuals,
                top_species
            FROM province_statistics;
            