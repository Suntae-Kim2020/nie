#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')  # GUI 없는 백엔드 사용
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import re
import PyPDF2
from collections import Counter
import os
import json
from datetime import datetime
from PIL import Image, ImageDraw
import tempfile

app = Flask(__name__)
CORS(app)  # CORS 허용
app.config['MAX_CONTENT_LENGTH'] = 35 * 1024 * 1024  # 35MB 최대 파일 크기

# 한글 폰트 경로 설정 (환경에 따라 동적 탐지)
def get_korean_font_path():
    """한글 폰트 경로를 자동으로 찾습니다."""
    possible_paths = [
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',  # Ubuntu/Docker
        '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',  # Ubuntu/Docker
        '/System/Library/Fonts/AppleSDGothicNeo.ttc',  # macOS
        'C:/Windows/Fonts/malgun.ttf',  # Windows
        '/usr/share/fonts/nanum/NanumGothic.ttf',  # Alternative path
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    print("⚠️ 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
    return None

KOREAN_FONT_PATH = get_korean_font_path()

def serve_html_file(filename):
    """HTML 파일을 안전하게 서빙"""
    try:
        if not filename.endswith('.html'):
            filename += '.html'
        
        # Docker 환경에서는 /app 디렉토리 사용
        base_dir = '/app' if os.path.exists('/app') else os.getcwd()
        file_path = os.path.join(base_dir, filename)
        
        print(f"파일 경로 확인: {file_path}")
        print(f"파일 존재 여부: {os.path.exists(file_path)}")
        print(f"현재 디렉토리: {os.getcwd()}")
        print(f"디렉토리 내용: {os.listdir(base_dir)}")
        
        if not os.path.exists(file_path):
            return jsonify({
                'error': f'파일을 찾을 수 없습니다: {filename}',
                'path': file_path,
                'base_dir': base_dir,
                'files': os.listdir(base_dir)
            }), 404
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        from flask import Response
        return Response(content, mimetype='text/html')
        
    except Exception as e:
        print(f"HTML 파일 서빙 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'파일 읽기 오류: {str(e)}'}), 500

# 사용자 정의 불용어 저장 파일 경로
USER_STOPWORDS_FILE = 'user_stopwords.json'

def load_user_stopwords():
    """저장된 사용자 정의 불용어 로드"""
    try:
        if os.path.exists(USER_STOPWORDS_FILE):
            with open(USER_STOPWORDS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('stopwords', []))
        return set()
    except Exception as e:
        print(f"사용자 불용어 로드 오류: {e}")
        return set()

def save_user_stopwords(new_stopwords):
    """사용자 정의 불용어 저장"""
    try:
        # 기존 불용어 로드
        existing_stopwords = load_user_stopwords()
        
        # 새로운 불용어 추가
        updated_stopwords = existing_stopwords | new_stopwords
        
        # 저장할 데이터 구성
        data = {
            'stopwords': list(updated_stopwords),
            'last_updated': datetime.now().isoformat(),
            'total_count': len(updated_stopwords)
        }
        
        # 파일에 저장
        with open(USER_STOPWORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"사용자 불용어 저장 완료: {len(new_stopwords)}개 추가, 총 {len(updated_stopwords)}개")
        return True
    except Exception as e:
        print(f"사용자 불용어 저장 오류: {e}")
        return False

def get_user_stopwords_for_display():
    """화면 표시용 사용자 불용어 목록 반환"""
    user_stopwords = load_user_stopwords()
    return ', '.join(sorted(user_stopwords)) if user_stopwords else ''

def get_korean_stopwords():
    """한국어 불용어 목록 (확장된 일반적인 불용어 사전)"""
    return set([
        # 조사
        '이', '가', '을', '를', '에', '에서', '로', '으로', '와', '과', '의', '도', '은', '는',
        '부터', '까지', '에게', '께', '한테', '에게서', '께서', '로서', '로써', '처럼', '같이',
        '만큼', '보다', '밖에', '뿐', '조차', '마저', '라도', '나마', '이나', '이라도',
        
        # 어미
        '다', '이다', '었다', '았다', '겠다', '하다', '되다', '있다', '없다', '같다', '이다',
        '한다', '된다', '한다', '말다', '이며', '이고', '이거나', '거나', '든지', '던지',
        
        # 대명사
        '그', '저', '이', '것', '그것', '저것', '이것', '여기', '거기', '저기', '이곳', '그곳',
        '저곳', '누구', '무엇', '언제', '어디', '어떻게', '왜', '어느', '얼마', '몇',
        
        # 동사/형용사 기본형
        '하다', '되다', '있다', '없다', '이다', '아니다', '그렇다', '이렇다', '저렇다',
        '크다', '작다', '좋다', '나쁘다', '높다', '낮다', '많다', '적다', '길다', '짧다',
        
        # 부사
        '더', '덜', '가장', '매우', '너무', '정말', '진짜', '참', '꽤', '상당히', '아주',
        '조금', '약간', '살짝', '완전', '전혀', '별로', '거의', '대략', '약', '한',
        '또', '다시', '또다시', '또한', '역시', '역시나', '물론', '당연히', '확실히',
        
        # 접속사
        '그리고', '그런데', '그러나', '하지만', '그래서', '따라서', '그러므로', '왜냐하면',
        '만약', '만일', '비록', '설령', '아무리', '혹시', '혹은', '또는', '아니면',
        
        # 감탄사
        '아', '어', '오', '우', '에', '와', '어머', '어머나', '어머니', '어이', '음', '흠',
        
        # 의존명사
        '것', '수', '점', '개', '번', '줄', '때', '시', '곳', '데', '바', '뿐', '지', '듯',
        
        # 기타 고빈도 기능어
        '등', '같은', '다른', '새로운', '이런', '저런', '그런', '어떤', '모든', '각', '여러',
        '일부', '전체', '전부', '부분', '대부분', '소부분', '약간의', '많은', '적은',
        '있는', '없는', '한', '두', '세', '네', '다섯', '첫', '둘째', '셋째', '마지막',
        
        # 추가 불용어 (사용자 요청)
        '있습니다', '대한', '있도록', '특히', '되는', '통한', '방면에서', '제공합니다', 
        '이상', '관련', '같은', '이런', '위한', '대해', '통해', '위해', '때문에', '인해',
        '따른', '따라', '경우', '때문', '관해', '대해서', '에서의', '으로서', '로서의',
        '에서는', '에는', '으로의', '로의', '에의', '만의', '들의', '들은', '들이',
        '들을', '라는', '이라는', '다는', '한다는', '된다는', '있다는', '없다는'
    ])

def get_english_stopwords():
    """영어 불용어 목록 (확장된 일반적인 불용어 사전)"""
    return set([
        # 관사
        'a', 'an', 'the',
        
        # 접속사
        'and', 'or', 'but', 'nor', 'for', 'so', 'yet', 'because', 'since', 'as', 'while',
        'although', 'though', 'unless', 'until', 'before', 'after', 'when', 'where',
        'however', 'therefore', 'moreover', 'furthermore', 'nevertheless', 'nonetheless',
        
        # 전치사
        'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'about', 'into',
        'through', 'during', 'before', 'after', 'above', 'below', 'up', 'down', 'out',
        'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
        'between', 'among', 'across', 'around', 'behind', 'beside', 'beyond', 'inside',
        'outside', 'toward', 'towards', 'within', 'without', 'upon', 'against',
        
        # be동사
        'is', 'are', 'was', 'were', 'be', 'been', 'being',
        
        # 조동사
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'done',
        'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall',
        
        # 대명사
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers',
        'ours', 'theirs', 'myself', 'yourself', 'himself', 'herself', 'itself',
        'ourselves', 'yourselves', 'themselves', 'this', 'that', 'these', 'those',
        'who', 'whom', 'whose', 'which', 'what', 'where', 'when', 'why', 'how',
        
        # 기타 고빈도 기능어
        'not', 'no', 'nor', 'yes', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
        'other', 'some', 'such', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
        'just', 'now', 'also', 'back', 'even', 'still', 'way', 'well', 'get', 'go',
        'know', 'take', 'see', 'come', 'think', 'say', 'get', 'make', 'go', 'know',
        'take', 'see', 'come', 'could', 'there', 'use', 'her', 'would', 'make',
        'like', 'into', 'time', 'has', 'look', 'two', 'more', 'go', 'no', 'way',
        'could', 'my', 'than', 'first', 'been', 'call', 'who', 'oil', 'sit', 'now',
        'find', 'long', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part'
    ])

def process_text(text, max_words=100, custom_stopwords=None):
    """텍스트 전처리 및 단어 추출"""
    print(f"원본 텍스트 길이: {len(text)}")
    
    # 특수문자 제거 및 소문자 변환
    cleaned_text = re.sub(r'[^\w\s가-힣]', ' ', text.lower())
    words = cleaned_text.split()
    
    print(f"초기 단어 수: {len(words)}")
    
    # 불용어 목록 준비
    korean_stopwords = get_korean_stopwords()
    english_stopwords = get_english_stopwords()
    
    # 저장된 사용자 불용어 로드
    saved_user_stopwords = load_user_stopwords()
    print(f"저장된 사용자 불용어: {len(saved_user_stopwords)}개")
    
    # 새로운 사용자 정의 불용어 처리
    new_custom_stopwords = set()
    if custom_stopwords:
        new_custom_stopwords = set([word.strip().lower() for word in custom_stopwords.split(',') if word.strip()])
        print(f"새로운 사용자 정의 불용어: {new_custom_stopwords}")
        
        # 새로운 불용어 저장
        if new_custom_stopwords:
            save_user_stopwords(new_custom_stopwords)
    
    # 모든 불용어 합치기 (기본 + 저장된 + 새로운)
    all_stopwords = korean_stopwords | english_stopwords | saved_user_stopwords | new_custom_stopwords
    print(f"전체 불용어 수: {len(all_stopwords)}")
    
    filtered_words = []
    for word in words:
        if (len(word) >= 2 and 
            word not in all_stopwords and 
            not word.isdigit()):
            filtered_words.append(word)
    
    print(f"필터링 후 단어 수: {len(filtered_words)}")
    
    # 단어 빈도 계산
    word_freq = Counter(filtered_words)
    most_common = word_freq.most_common(max_words)
    
    print(f"최종 추출 단어 수: {len(most_common)}")
    print(f"상위 10개 단어: {most_common[:10]}")
    
    return dict(most_common)

def extract_text_from_pdf(file):
    """PDF에서 텍스트 추출"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + " "
        
        print(f"PDF에서 추출된 텍스트 길이: {len(text)}")
        return text.strip()
    
    except Exception as e:
        print(f"PDF 처리 오류: {e}")
        raise Exception(f"PDF 파일을 처리할 수 없습니다: {str(e)}")

def create_shape_mask(shape, width, height):
    """다양한 모양의 마스크 생성"""
    mask = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(mask)
    
    center_x, center_y = width // 2, height // 2
    # 원형일 때는 더 크게, 다른 모양일 때는 적당히
    if shape == 'circle':
        size = min(width, height) // 2.2  # 원형을 더 크게
    else:
        size = min(width, height) // 3
    
    if shape == 'circle':
        # 완벽한 원형 생성
        draw.ellipse([center_x - size, center_y - size, 
                     center_x + size, center_y + size], fill='black')
        # 가장자리를 부드럽게 하기 위해 작은 원 추가
        for i in range(3):
            offset = i * 2
            draw.ellipse([center_x - size + offset, center_y - size + offset, 
                         center_x + size - offset, center_y + size - offset], fill='black')
    
    elif shape == 'heart':
        # 하트 모양 그리기
        heart_points = []
        for t in np.arange(0, 2 * np.pi, 0.1):
            x = 16 * np.sin(t)**3
            y = 13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t)
            heart_points.append((center_x + x * size//20, center_y - y * size//20))
        draw.polygon(heart_points, fill='black')
    
    elif shape == 'diamond':
        points = [
            (center_x, center_y - size),
            (center_x + size, center_y),
            (center_x, center_y + size),
            (center_x - size, center_y)
        ]
        draw.polygon(points, fill='black')
    
    elif shape == 'triangle':
        points = [
            (center_x, center_y - size),
            (center_x + size, center_y + size//2),
            (center_x - size, center_y + size//2)
        ]
        draw.polygon(points, fill='black')
    
    elif shape == 'pentagon':
        points = []
        for i in range(5):
            angle = i * 2 * np.pi / 5 - np.pi/2
            x = center_x + size * np.cos(angle)
            y = center_y + size * np.sin(angle)
            points.append((x, y))
        draw.polygon(points, fill='black')
    
    elif shape == 'star':
        points = []
        for i in range(10):
            angle = i * np.pi / 5 - np.pi/2
            radius = size if i % 2 == 0 else size * 0.4
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            points.append((x, y))
        draw.polygon(points, fill='black')
    
    return np.array(mask)

def create_wordcloud(word_freq, shape='circle', color_mode='color', width=600, height=450):
    """워드클라우드 생성"""
    print(f"워드클라우드 생성: {shape}, {color_mode}, {width}x{height}")
    
    # 색상 설정
    if color_mode == 'grayscale':
        colormap = 'gray'
    else:
        colormap = 'viridis'
    
    # WordCloud 기본 설정
    wc_config = {
        'width': width,
        'height': height,
        'background_color': 'white',
        'max_words': len(word_freq),
        'colormap': colormap,
        'font_path': KOREAN_FONT_PATH if KOREAN_FONT_PATH and os.path.exists(KOREAN_FONT_PATH) else None,
        'relative_scaling': 0.5,
        'min_font_size': 12,
        'max_font_size': 100,
        'prefer_horizontal': 0.7
    }
    
    # 모든 모양에 대해 마스크 사용 (원형 포함)
    mask = create_shape_mask(shape, width, height)
    wc_config['mask'] = mask
    # 마스크 사용시 추가 설정
    wc_config['mode'] = 'RGBA'
    wc_config['max_words'] = len(word_freq)
    wc_config['contour_width'] = 0
    wc_config['contour_color'] = 'steelblue'
    
    # 워드클라우드 생성
    wc = WordCloud(**wc_config).generate_from_frequencies(word_freq)
    
    # 이미지 생성
    plt.figure(figsize=(width/100, height/100))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    
    # 이미지를 base64로 인코딩
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
    img_buffer.seek(0)
    
    img_b64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    return img_b64

@app.route('/')
def index():
    """메인 포털 페이지"""
    return serve_html_file('index.html')

@app.route('/wordcloud')
def wordcloud_page():
    """워드클라우드 페이지"""
    return render_template('wordcloud.html')

# 조류 충돌 분석 페이지들
@app.route('/bird-analysis')
def bird_analysis():
    """조류 충돌 분석 메인"""
    return serve_html_file('bird_collision_analysis.html')

@app.route('/bird-dashboard')  
def bird_dashboard():
    """조류 충돌 대시보드"""
    return serve_html_file('bird_collision_dashboard.html')

@app.route('/bird-detailed-analysis')
def bird_detailed_analysis():
    """조류 충돌 상세 분석"""
    return serve_html_file('bird_collision_detailed_analysis.html')

@app.route('/bird-map')
def bird_map():
    """조류 충돌 지도"""
    return serve_html_file('bird_collision_map.html')

# NIE 다국어 서비스
@app.route('/nie-multilingual')
def nie_multilingual():
    """NIE 다국어 서비스"""
    return serve_html_file('nie_multilingual.html')

# 기타 페이지들
@app.route('/policy-recommendations')
def policy_recommendations():
    """정책 제안"""
    return serve_html_file('policy_recommendations.html')

@app.route('/monitoring-dashboard')
def monitoring_dashboard():
    """실시간 모니터링 대시보드"""
    return serve_html_file('real_time_monitoring_dashboard.html')


@app.route('/favicon.ico')
def favicon():
    """Favicon 처리"""
    return '', 204  # No Content

@app.route('/health')
def health():
    """Health check for Docker"""
    return jsonify({'status': 'healthy', 'service': 'wordcloud'}), 200

@app.errorhandler(404)
def not_found(error):
    """404 에러 처리"""
    return jsonify({'error': '페이지를 찾을 수 없습니다.'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500 에러 처리"""
    print(f"서버 내부 오류: {error}")
    import traceback
    traceback.print_exc()
    return jsonify({
        'error': '서버 내부 오류가 발생했습니다.', 
        'detail': str(error) if app.debug else None
    }), 500

@app.route('/generate', methods=['POST'])
def generate_wordcloud():
    """워드클라우드 생성 API"""
    try:
        # 파라미터 받기
        text = request.form.get('text', '')
        shape = request.form.get('shape', 'circle')
        color_mode = request.form.get('color_mode', 'color')
        word_count = int(request.form.get('word_count', 100))
        canvas_size = request.form.get('canvas_size', '600,450')
        custom_stopwords = request.form.get('custom_stopwords', '')
        
        width, height = map(int, canvas_size.split(','))
        
        # PDF 파일 처리
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file and pdf_file.filename.endswith('.pdf'):
                text = extract_text_from_pdf(pdf_file)
        
        if not text or len(text.strip()) < 50:
            return jsonify({'error': '최소 50자 이상의 텍스트가 필요합니다.'}), 400
        
        # 텍스트 처리
        word_freq = process_text(text, word_count, custom_stopwords)
        
        if not word_freq:
            return jsonify({'error': '분석할 수 있는 단어를 찾을 수 없습니다.'}), 400
        
        # 워드클라우드 생성
        img_b64 = create_wordcloud(word_freq, shape, color_mode, width, height)
        
        return jsonify({
            'success': True,
            'image': img_b64,
            'word_count': len(word_freq),
            'shape': shape,
            'message': f'워드클라우드 생성 완료! ({len(word_freq)}개 단어)'
        })
    
    except Exception as e:
        print(f"오류 발생: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_saved_stopwords')
def get_saved_stopwords():
    """저장된 사용자 불용어 조회"""
    try:
        user_stopwords = load_user_stopwords()
        stopwords_text = ', '.join(sorted(user_stopwords)) if user_stopwords else ''
        
        return jsonify({
            'success': True,
            'stopwords': stopwords_text,
            'count': len(user_stopwords)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear_saved_stopwords', methods=['POST'])
def clear_saved_stopwords():
    """저장된 사용자 불용어 초기화"""
    try:
        if os.path.exists(USER_STOPWORDS_FILE):
            os.remove(USER_STOPWORDS_FILE)
        
        return jsonify({
            'success': True,
            'message': '저장된 불용어가 모두 삭제되었습니다.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download')
def download_wordcloud():
    """워드클라우드 이미지 다운로드"""
    # 세션이나 임시 저장소에서 이미지를 가져와서 다운로드 제공
    # 현재는 간단한 구현
    return jsonify({'message': '다운로드 기능은 프론트엔드에서 구현됩니다.'})

if __name__ == '__main__':
    print("Flask WordCloud 서버 시작...")
    print(f"한글 폰트 경로: {KOREAN_FONT_PATH or '폰트를 찾을 수 없음'}")
    if KOREAN_FONT_PATH:
        print(f"폰트 파일 존재: {os.path.exists(KOREAN_FONT_PATH)}")
    else:
        print("폰트 파일 존재: False (기본 폰트 사용)")
    
    # Cloud Run에서는 PORT 환경 변수를 사용
    port = int(os.environ.get('PORT', 5000))
    print(f"서버 포트: {port}")
    
    app.run(debug=False, host='0.0.0.0', port=port)