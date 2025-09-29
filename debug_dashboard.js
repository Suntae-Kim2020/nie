// 대시보드 디버깅용 스크립트

console.log('🐦 대시보드 디버깅 시작');

// 전역 변수 확인
function checkGlobalVariables() {
    console.log('전역 변수 상태:');
    console.log('- dashboardData:', typeof dashboardData, dashboardData?.length || 'undefined');
    console.log('- filteredDashboardData:', typeof filteredDashboardData, filteredDashboardData?.length || 'undefined');
    console.log('- dashboardCharts:', typeof dashboardCharts, Object.keys(dashboardCharts || {}));
}

// 데이터 로딩 테스트
async function testDataLoading() {
    console.log('데이터 로딩 테스트 시작...');
    
    try {
        const response = await fetch('./bird_analysis_results.json');
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ 데이터 로드 성공:', data);
            console.log('- raw_data 길이:', data.raw_data?.length);
            console.log('- 첫 3개 레코드:', data.raw_data?.slice(0, 3));
            return data;
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('❌ 데이터 로드 실패:', error);
        return null;
    }
}

// DOM 요소 확인
function checkDOMElements() {
    const elements = [
        'yearFilter', 'sidoFilter', 'facilityFilterDash', 'seasonFilter',
        'totalAccidents', 'highRiskAreas', 'affectedSpecies',
        'monthlyTrendChart', 'sidoDistributionChart', 'speciesDistributionChart', 'facilityChart',
        'tableBody'
    ];
    
    console.log('DOM 요소 확인:');
    elements.forEach(id => {
        const element = document.getElementById(id);
        console.log(`- ${id}:`, element ? '✅ 존재' : '❌ 없음');
    });
}

// Chart.js 확인
function checkChartJS() {
    console.log('Chart.js 상태:');
    console.log('- Chart 객체:', typeof Chart);
    console.log('- Chart 버전:', Chart.version || 'unknown');
}

// 전체 진단 실행
function runDiagnostics() {
    console.log('🔍 대시보드 진단 시작');
    console.log('='.repeat(50));
    
    checkGlobalVariables();
    console.log('');
    
    checkChartJS();
    console.log('');
    
    checkDOMElements();
    console.log('');
    
    testDataLoading().then(data => {
        if (data) {
            console.log('✅ 모든 진단 완료 - 데이터 사용 가능');
        } else {
            console.log('⚠️ 진단 완료 - 데이터 로드 실패');
        }
    });
}

// 페이지 로드 후 진단 실행
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(runDiagnostics, 1000);
    });
} else {
    setTimeout(runDiagnostics, 1000);
}