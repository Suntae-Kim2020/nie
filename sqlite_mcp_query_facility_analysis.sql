-- SQLite MCP 테스트 쿼리: 시설물별 분석
-- 생성일: 2025-09-29 15:43:42


            SELECT 
                facility_type,
                incidents,
                percentage,
                species_affected,
                with_bird_saver,
                without_bird_saver
            FROM facility_analysis;
            