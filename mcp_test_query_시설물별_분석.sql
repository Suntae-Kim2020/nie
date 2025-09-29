-- MCP 테스트 쿼리: 시설물별_분석
-- 생성일: 2025-09-23 17:39:09


-- 시설물별 상세 분석
SELECT 
    facility_type as 시설물유형,
    COUNT(*) as 사고건수,
    ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM bird_collision_incidents)), 2) as 비율_퍼센트,
    COUNT(DISTINCT korean_common_name) as 영향받은_조류종수,
    AVG(individual_count) as 평균_개체수,
    SUM(CASE WHEN bird_saver_installed THEN 1 ELSE 0 END) as 버드세이버_설치건수
FROM bird_collision_incidents
GROUP BY facility_type
ORDER BY 사고건수 DESC;
