-- MCP 테스트 쿼리: 핫스팟_분석
-- 생성일: 2025-09-23 17:39:09


-- 지역별 핫스팟 분석 (PostGIS 활용)
SELECT 
    province as 시도,
    total_incidents as 총_사고건수,
    ST_AsText(center_point) as 중심좌표,
    array_length(species_list, 1) as 조류종_수
FROM v_regional_hotspots
ORDER BY total_incidents DESC;
