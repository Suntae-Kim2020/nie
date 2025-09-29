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

# Set maximum request size to 50MB to handle large text files
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

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

# Error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "error": "Request Entity Too Large",
        "message": "요청 크기가 너무 큽니다. 텍스트를 줄여주세요.",
        "max_size": "50MB",
        "status": "error"
    }), 413

@app.errorhandler(415)
def unsupported_media_type(error):
    return jsonify({
        "error": "Unsupported Media Type",
        "message": "지원하지 않는 Content-Type입니다. JSON 또는 form-data를 사용해주세요.",
        "supported_types": ["application/json", "multipart/form-data", "application/x-www-form-urlencoded", "text/plain"],
        "status": "error"
    }), 415

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "서버 내부 오류가 발생했습니다.",
        "status": "error"
    }), 500

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
        
        # Request 크기 체크
        content_length = request.content_length
        if content_length and content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({
                "error": "Request too large",
                "message": f"요청 크기가 {content_length/1024/1024:.1f}MB로 너무 큽니다. 최대 50MB까지 허용됩니다.",
                "status": "error"
            }), 413
        
        # 디버깅: 요청 정보 로깅
        print(f"🔍 Request debugging:")
        print(f"   Content-Type: {request.content_type}")
        print(f"   Content-Length: {request.content_length}")
        print(f"   Method: {request.method}")
        print(f"   Is JSON: {request.is_json}")
        print(f"   Form keys: {list(request.form.keys()) if request.form else []}")
        print(f"   Form data: {dict(request.form) if request.form else {}}")
        print(f"   Files keys: {list(request.files.keys()) if request.files else []}")
        print(f"   Args keys: {list(request.args.keys()) if request.args else []}")
        print(f"   Raw data length: {len(request.get_data()) if request.get_data() else 0}")
        
        # 요청 헤더도 확인
        print(f"   Headers:")
        for header, value in request.headers:
            if header.lower() in ['content-type', 'content-length', 'accept', 'user-agent']:
                print(f"     {header}: {value}")
        
        # 다양한 Content-Type 지원
        text = ''
        
        try:
            # JSON 요청 처리
            if request.is_json:
                data = request.get_json()
                print(f"📋 JSON data received: {data}")
                if data:
                    text = data.get('text', '')
                    print(f"📄 Text from JSON: {len(text)} characters")
            
            # Form data 요청 처리 (파일 업로드 등)
            elif request.content_type and 'multipart/form-data' in request.content_type:
                print(f"📤 Processing multipart/form-data")
                text = request.form.get('text', '')
                print(f"📝 Text from form: '{text[:100]}...' ({len(text)} chars)")
                
                # 파일이 업로드된 경우
                if 'file' in request.files:
                    file = request.files['file']
                    print(f"📁 File found: {file.filename if file else 'None'}")
                    if file and file.filename:
                        try:
                            file_content = None
                            
                            # PDF 파일 처리
                            if file.filename.lower().endswith('.pdf'):
                                try:
                                    import PyPDF2
                                    pdf_reader = PyPDF2.PdfReader(file)
                                    pdf_text = ""
                                    for page in pdf_reader.pages:
                                        pdf_text += page.extract_text() + "\n"
                                    file_content = pdf_text
                                    print(f"📁 PDF processed: {file.filename}, pages: {len(pdf_reader.pages)}")
                                except ImportError:
                                    # PyPDF2가 없으면 에러 메시지 반환
                                    return jsonify({
                                        "error": "PDF processing not available",
                                        "message": "PDF 처리 라이브러리가 설치되지 않았습니다. 텍스트 파일을 사용해주세요.",
                                        "status": "error"
                                    }), 400
                                except Exception as pdf_error:
                                    return jsonify({
                                        "error": "PDF processing failed",
                                        "message": f"PDF 파일 처리 중 오류: {str(pdf_error)}",
                                        "status": "error"
                                    }), 400
                            else:
                                # 텍스트 파일 처리 (여러 인코딩 시도)
                                file_bytes = file.read()
                                
                                # UTF-8 먼저 시도
                                try:
                                    file_content = file_bytes.decode('utf-8')
                                except UnicodeDecodeError:
                                    # UTF-8이 실패하면 다른 인코딩들 시도
                                    encodings = ['cp949', 'euc-kr', 'latin1', 'utf-16']
                                    for encoding in encodings:
                                        try:
                                            file_content = file_bytes.decode(encoding)
                                            print(f"📁 File decoded with {encoding} encoding")
                                            break
                                        except UnicodeDecodeError:
                                            continue
                            
                            if file_content is None:
                                raise Exception("파일 인코딩을 인식할 수 없습니다")
                            
                            text = file_content if not text else text + '\n' + file_content
                            print(f"📁 File uploaded: {file.filename}, size: {len(file_content)} chars")
                            
                        except Exception as file_error:
                            print(f"❌ File reading error: {str(file_error)}")
                            return jsonify({
                                "error": "File reading failed",
                                "message": f"파일을 읽을 수 없습니다: {str(file_error)}",
                                "status": "error"
                            }), 400
                
                # textarea 필드도 확인
                if not text and 'textarea' in request.form:
                    text = request.form.get('textarea', '')
                    print(f"📝 Text from textarea: {len(text)} characters")
            
            # application/x-www-form-urlencoded 처리
            elif request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
                print(f"📤 Processing form-urlencoded")
                text = request.form.get('text', '')
                if not text:
                    text = request.form.get('textarea', '')
                print(f"📝 Text from form: {len(text)} characters")
            
            # Raw text 처리
            elif request.content_type and 'text/plain' in request.content_type:
                print(f"📤 Processing plain text")
                text = request.get_data(as_text=True)
                print(f"📝 Raw text: {len(text)} characters")
            
            # 기본값 처리 - 모든 가능한 필드 확인
            else:
                print(f"📤 Processing fallback options")
                # 여러 필드명 시도
                possible_fields = ['text', 'textarea', 'content', 'data']
                for field in possible_fields:
                    if request.form and field in request.form:
                        text = request.form.get(field, '')
                        if text:
                            print(f"📝 Text found in field '{field}': {len(text)} characters")
                            break
                
                # URL 파라미터도 확인
                if not text:
                    for field in possible_fields:
                        if field in request.args:
                            text = request.args.get(field, '')
                            if text:
                                print(f"📝 Text found in URL param '{field}': {len(text)} characters")
                                break
                
                if not text:
                    print(f"⚠️ No text found. Content-Type: {request.content_type}")
                    print(f"   Available form fields: {dict(request.form) if request.form else 'None'}")
                    print(f"   Available URL params: {dict(request.args) if request.args else 'None'}")
                    
                    return jsonify({
                        "error": "Unsupported Content-Type or no text found",
                        "message": f"지원하지 않는 Content-Type이거나 텍스트를 찾을 수 없습니다: {request.content_type}",
                        "supported_types": ["application/json", "multipart/form-data", "application/x-www-form-urlencoded", "text/plain"],
                        "available_fields": list(request.form.keys()) if request.form else [],
                        "status": "error"
                    }), 415
            
        except Exception as parse_error:
            print(f"❌ Request parsing error: {str(parse_error)}")
            return jsonify({
                "error": "Request parsing failed",
                "message": f"요청 파싱 중 오류가 발생했습니다: {str(parse_error)}",
                "status": "error"
            }), 400
        
        if not text or not text.strip():
            return jsonify({"error": "No text provided or text is empty"}), 400
        
        # 텍스트 길이 체크 및 제한
        text_size_mb = len(text.encode('utf-8')) / (1024 * 1024)
        print(f"📊 Text size: {text_size_mb:.2f}MB, length: {len(text)} characters")
        
        if text_size_mb > 5:  # 5MB 이상의 텍스트는 자름
            print("⚠️ Text too large, truncating to 5MB...")
            text = text[:int(5 * 1024 * 1024 / 4)]  # UTF-8에서 한 글자당 평균 4바이트로 추정
            print(f"✂️ Text truncated to {len(text)} characters")
        
        # WordCloud 생성 (메모리 효율적 설정)
        try:
            print(f"🎨 Generating WordCloud with {len(text)} characters...")
            print(f"🔤 Korean font path: {KOREAN_FONT_PATH}")
            
            # 메모리 사용량을 줄이기 위해 이미지 크기 조정
            if text_size_mb > 2:
                width, height = 600, 300  # 큰 텍스트는 작은 이미지
                max_words = 80
                dpi = 100
            elif text_size_mb > 1:
                width, height = 700, 350
                max_words = 90
                dpi = 120
            else:
                width, height = 800, 400
                max_words = 100
                dpi = 150
            
            print(f"📏 Image settings: {width}x{height}, max_words: {max_words}, dpi: {dpi}")
            
            wordcloud = WordCloud(
                font_path=KOREAN_FONT_PATH,
                width=width,
                height=height,
                background_color='white',
                max_words=max_words,
                relative_scaling=0.5,
                colormap='viridis',
                collocations=False,  # 메모리 절약
                prefer_horizontal=0.7
            ).generate(text)
            
            print("✅ WordCloud generated successfully")
            
            # 이미지를 base64로 변환 (메모리 효율적)
            img_buffer = io.BytesIO()
            plt.figure(figsize=(width/100, height/100))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=dpi, 
                       facecolor='white', edgecolor='none')
            plt.close()  # 메모리 해제
            
            print("💾 Image saved to buffer")
            
            img_buffer.seek(0)
            img_data = img_buffer.getvalue()
            img_size_mb = len(img_data) / (1024 * 1024)
            print(f"🖼️ Generated image size: {img_size_mb:.2f}MB")
            
            img_str = base64.b64encode(img_data).decode()
            
            # 메모리 정리
            img_buffer.close()
            del img_data
            
            print("✅ Image encoded to base64 successfully")
            
            return jsonify({
                "status": "success",
                "image": f"data:image/png;base64,{img_str}",
                "info": {
                    "text_size_mb": round(text_size_mb, 2),
                    "image_size_mb": round(img_size_mb, 2),
                    "max_words": max_words
                }
            })
            
        except Exception as wc_error:
            print(f"❌ WordCloud generation error: {str(wc_error)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "WordCloud generation failed",
                "message": str(wc_error),
                "status": "error"
            }), 500
        
    except Exception as e:
        print(f"❌ Server error: {str(e)}")
        import traceback
        traceback.print_exc()
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