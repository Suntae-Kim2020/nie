#!/usr/bin/env python3
"""
HTTP-based SQLite MCP Server for ChatGPT Desktop
조류충돌 데이터베이스에 대한 HTTP MCP 서버 구현
"""

import sqlite3
import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, List, Any, Optional
import secrets

class SQLiteHTTPMCPServer:
    def __init__(self, database_path: str, api_key: str = None):
        self.database_path = database_path
        self.api_key = api_key or secrets.token_urlsafe(32)
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_routes()
        
    def connect_db(self):
        """데이터베이스 연결"""
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            return None
    
    def authenticate(self, auth_header: str) -> bool:
        """API 키 인증"""
        if not auth_header:
            return False
        
        # Bearer token 방식
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return token == self.api_key
        
        # Simple API key 방식
        return auth_header == self.api_key
    
    def execute_query(self, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """쿼리 실행"""
        conn = self.connect_db()
        if not conn:
            return {"error": "Database connection failed"}
        
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                data = [dict(row) for row in results]
                return {
                    "success": True,
                    "data": data,
                    "row_count": len(data)
                }
            else:
                conn.commit()
                return {
                    "success": True,
                    "affected_rows": cursor.rowcount
                }
                
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()
    
    def get_schema(self) -> Dict[str, Any]:
        """데이터베이스 스키마 정보"""
        conn = self.connect_db()
        if not conn:
            return {"error": "Database connection failed"}
        
        try:
            cursor = conn.cursor()
            
            # 테이블 목록
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [{"name": row[0]} for row in cursor.fetchall()]
            
            # 뷰 목록
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
            views = [{"name": row[0]} for row in cursor.fetchall()]
            
            schema = {
                "tables": tables,
                "views": views
            }
            
            # 각 테이블의 컬럼 정보
            for table in tables:
                table_name = table["name"]
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [dict(zip([col[0] for col in cursor.description], row)) 
                          for row in cursor.fetchall()]
                schema[f"{table_name}_columns"] = columns
            
            return {"success": True, "schema": schema}
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()
    
    def setup_routes(self):
        """Flask 라우트 설정"""
        
        @self.app.route('/mcp/tools', methods=['GET'])
        def list_tools():
            # 인증 확인
            auth_header = request.headers.get('Authorization', '')
            if not self.authenticate(auth_header):
                return jsonify({"error": "Unauthorized"}), 401
            
            return jsonify({
                "tools": [
                    {
                        "name": "execute_sql",
                        "description": "Execute SQL queries on the bird collision database",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "SQL query to execute"
                                },
                                "params": {
                                    "type": "array",
                                    "description": "Query parameters (optional)"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_schema",
                        "description": "Get database schema information",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            })
        
        @self.app.route('/mcp/tools/call', methods=['POST'])
        def call_tool():
            # 인증 확인
            auth_header = request.headers.get('Authorization', '')
            if not self.authenticate(auth_header):
                return jsonify({"error": "Unauthorized"}), 401
            
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            tool_name = data.get("name")
            tool_params = data.get("arguments", {})
            
            if tool_name == "execute_sql":
                query = tool_params.get("query")
                query_params = tool_params.get("params")
                result = self.execute_query(query, query_params)
                
                return jsonify({
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                })
            
            elif tool_name == "get_schema":
                result = self.get_schema()
                return jsonify({
                    "content": [
                        {
                            "type": "text", 
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                })
            
            return jsonify({"error": "Unknown tool"}), 400
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy", "database": os.path.exists(self.database_path)})
        
        @self.app.route('/auth/info', methods=['GET'])
        def auth_info():
            return jsonify({
                "auth_type": "bearer_token",
                "api_key": self.api_key,
                "instructions": "Use 'Authorization: Bearer <api_key>' header"
            })

def main():
    """메인 함수"""
    database_path = os.environ.get("DATABASE_PATH", "/Users/suntaekim/nie/bird_collision_mcp.db")
    api_key = os.environ.get("MCP_API_KEY", secrets.token_urlsafe(32))
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "127.0.0.1")
    
    if not os.path.exists(database_path):
        print(f"❌ Database file not found: {database_path}")
        return
    
    server = SQLiteHTTPMCPServer(database_path, api_key)
    
    print(f"🚀 SQLite MCP HTTP Server starting...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"🔑 API Key: {api_key}")
    print(f"💾 Database: {database_path}")
    print(f"🔗 Health Check: http://{host}:{port}/health")
    print(f"📋 Tools List: http://{host}:{port}/mcp/tools")
    print(f"ℹ️  Auth Info: http://{host}:{port}/auth/info")
    print(f"🔐 Authorization Header: Bearer {api_key}")
    
    server.app.run(host=host, port=port, debug=True)

if __name__ == "__main__":
    main()