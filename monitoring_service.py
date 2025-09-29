#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIE 프로젝트 모니터링 서비스
시스템 상태 모니터링 및 메트릭 수집
"""

from flask import Flask, jsonify, render_template_string
import psutil
import time
import threading
from datetime import datetime
import os
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 시스템 메트릭 저장
system_metrics = {
    'cpu_percent': 0,
    'memory_percent': 0,
    'disk_usage': 0,
    'network_sent': 0,
    'network_recv': 0,
    'uptime': 0,
    'last_update': None
}

def collect_metrics():
    """시스템 메트릭 수집"""
    global system_metrics
    
    while True:
        try:
            # CPU 사용률
            system_metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            system_metrics['memory_percent'] = memory.percent
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            system_metrics['disk_usage'] = (disk.used / disk.total) * 100
            
            # 네트워크 통계
            net_io = psutil.net_io_counters()
            system_metrics['network_sent'] = net_io.bytes_sent
            system_metrics['network_recv'] = net_io.bytes_recv
            
            # 업타임
            boot_time = psutil.boot_time()
            system_metrics['uptime'] = time.time() - boot_time
            
            # 마지막 업데이트 시간
            system_metrics['last_update'] = datetime.now().isoformat()
            
            logger.info(f"메트릭 수집 완료 - CPU: {system_metrics['cpu_percent']}%, 메모리: {system_metrics['memory_percent']}%")
            
        except Exception as e:
            logger.error(f"메트릭 수집 중 오류: {e}")
        
        time.sleep(30)  # 30초마다 수집

@app.route('/')
def dashboard():
    """모니터링 대시보드"""
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NIE 모니터링 대시보드</title>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="30">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; color: #333; margin-bottom: 30px; }
            .metric-card { 
                background: white; 
                border-radius: 8px; 
                padding: 20px; 
                margin: 10px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                display: inline-block;
                width: 280px;
                vertical-align: top;
            }
            .metric-title { font-size: 18px; font-weight: bold; color: #666; margin-bottom: 10px; }
            .metric-value { font-size: 32px; font-weight: bold; color: #2196F3; }
            .metric-unit { font-size: 16px; color: #888; }
            .status-good { color: #4CAF50; }
            .status-warning { color: #FF9800; }
            .status-critical { color: #F44336; }
            .timestamp { text-align: center; color: #888; margin-top: 30px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🖥️ NIE 시스템 모니터링</h1>
                <p>실시간 시스템 상태 및 성능 메트릭</p>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">CPU 사용률</div>
                <div class="metric-value {{ 'status-critical' if cpu_percent > 80 else 'status-warning' if cpu_percent > 60 else 'status-good' }}">
                    {{ "%.1f" | format(cpu_percent) }}
                </div>
                <div class="metric-unit">%</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">메모리 사용률</div>
                <div class="metric-value {{ 'status-critical' if memory_percent > 80 else 'status-warning' if memory_percent > 60 else 'status-good' }}">
                    {{ "%.1f" | format(memory_percent) }}
                </div>
                <div class="metric-unit">%</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">디스크 사용률</div>
                <div class="metric-value {{ 'status-critical' if disk_usage > 80 else 'status-warning' if disk_usage > 60 else 'status-good' }}">
                    {{ "%.1f" | format(disk_usage) }}
                </div>
                <div class="metric-unit">%</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">업타임</div>
                <div class="metric-value status-good">
                    {{ "%.1f" | format(uptime / 3600) }}
                </div>
                <div class="metric-unit">시간</div>
            </div>
            
            <div class="timestamp">
                마지막 업데이트: {{ last_update or '수집 중...' }}
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(dashboard_html, **system_metrics)

@app.route('/api/metrics')
def api_metrics():
    """API 엔드포인트로 메트릭 제공"""
    return jsonify(system_metrics)

@app.route('/api/health')
def health_check():
    """헬스체크 엔드포인트"""
    status = "healthy"
    
    # 간단한 헬스체크 로직
    if system_metrics['cpu_percent'] > 90:
        status = "critical"
    elif system_metrics['memory_percent'] > 90:
        status = "critical"
    elif system_metrics['cpu_percent'] > 70 or system_metrics['memory_percent'] > 70:
        status = "warning"
    
    return jsonify({
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'metrics': system_metrics
    })

@app.route('/api/services')
def services_status():
    """서비스 상태 확인"""
    services = {
        'flask_wordcloud': {'port': 5000, 'status': 'unknown'},
        'mcp_http': {'port': 8080, 'status': 'unknown'},
        'mcp_sqlite': {'port': 3000, 'status': 'unknown'},
        'monitoring': {'port': 9090, 'status': 'running'}
    }
    
    return jsonify({
        'services': services,
        'timestamp': datetime.now().isoformat()
    })

def main():
    """메인 함수"""
    logger.info("NIE 모니터링 서비스 시작 중...")
    
    # 메트릭 수집 스레드 시작
    metrics_thread = threading.Thread(target=collect_metrics, daemon=True)
    metrics_thread.start()
    logger.info("메트릭 수집 스레드 시작됨")
    
    # Flask 서버 시작
    port = int(os.environ.get('PORT', 9090))
    logger.info(f"모니터링 서비스가 포트 {port}에서 시작됩니다")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False
    )

if __name__ == '__main__':
    main()