#!/usr/bin/env python3
"""
Enhanced Flask app with WordCloud functionality for Cloud Run
"""

import os
import io
import base64
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 한글 폰트 경로 설정 (Cloud Run 환경 고려)
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

# 사용자 불용어 파일 경로
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

@app.route('/')
def index():
    try:
        return render_template('wordcloud.html')
    except Exception as e:
        # 템플릿이 없는 경우 기본 HTML 반환
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>NIE WordCloud Service</title>
        </head>
        <body>
            <h1>🚀 NIE WordCloud Service</h1>
            <p>서비스가 성공적으로 배포되었습니다!</p>
            <p>Korean Font Path: {KOREAN_FONT_PATH or 'Not found'}</p>
            <p>Error loading template: {str(e)}</p>
        </body>
        </html>
        """

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "korean_font_available": KOREAN_FONT_PATH is not None,
        "font_path": KOREAN_FONT_PATH
    }

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/generate', methods=['POST'])  
def generate():
    """기존 템플릿에서 사용하는 /generate 엔드포인트"""
    return generate_wordcloud()

@app.route('/generate_wordcloud', methods=['POST'])
def generate_wordcloud():
    try:
        # WordCloud 라이브러리를 동적으로 import (없으면 에러 처리)
        try:
            from wordcloud import WordCloud
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        except ImportError as e:
            return jsonify({
                "error": "WordCloud libraries not available",
                "message": str(e),
                "status": "error"
            }), 500
        
        data = request.get_json()
        text = data.get('text', 'Hello World 안녕하세요')
        
        if not text.strip():
            return jsonify({"error": "No text provided"}), 400
        
        # WordCloud 생성 (안전한 설정으로)
        try:
            print(f"Generating WordCloud with text: {text[:50]}...")
            print(f"Korean font path: {KOREAN_FONT_PATH}")
            
            wordcloud = WordCloud(
                font_path=KOREAN_FONT_PATH,
                width=800,
                height=400,
                background_color='white',
                max_words=100,
                relative_scaling=0.5,
                colormap='viridis'
            ).generate(text)
            
            print("WordCloud generated successfully")
            
            # 이미지를 base64로 변환
            img_buffer = io.BytesIO()
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
            plt.close()
            
            print("Image saved to buffer")
            
            img_buffer.seek(0)
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            print("Image encoded to base64")
            
            return jsonify({
                "status": "success",
                "image": f"data:image/png;base64,{img_str}"
            })
            
        except Exception as wc_error:
            print(f"WordCloud generation error: {str(wc_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "WordCloud generation failed",
                "message": str(wc_error),
                "status": "error"
            }), 500
        
    except Exception as e:
        return jsonify({
            "error": "Server error",
            "message": str(e),
            "status": "error"
        }), 500

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
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Enhanced Flask WordCloud app on port {port}")
    print(f"🔤 Korean Font: {KOREAN_FONT_PATH or 'Not available'}")
    app.run(debug=False, host='0.0.0.0', port=port)