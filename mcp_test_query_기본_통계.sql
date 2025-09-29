-- MCP 테스트 쿼리: 기본_통계
-- 생성일: 2025-09-23 17:39:09


-- 전체 통계 조회
SELECT 
    COUNT(*) as 총_사고건수,
    COUNT(DISTINCT korean_common_name) as 조류종_수,
    COUNT(DISTINCT province) as 시도_수,
    SUM(individual_count) as 총_개체수
FROM bird_collision_incidents;
