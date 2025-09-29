-- MCP 테스트 쿼리: 버드세이버_효과
-- 생성일: 2025-09-23 17:39:09


-- 버드세이버 설치 효과 분석
SELECT 
    bird_saver_installed as 버드세이버_설치여부,
    COUNT(*) as 사고건수,
    AVG(individual_count) as 평균_개체수,
    COUNT(DISTINCT korean_common_name) as 영향받은_종수
FROM bird_collision_incidents
WHERE bird_saver_installed IS NOT NULL
GROUP BY bird_saver_installed;
