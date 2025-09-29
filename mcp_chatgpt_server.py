#!/usr/bin/env python3
"""
ChatGPT Desktop 호환 MCP 서버
조류충돌 데이터베이스에 대한 ChatGPT Desktop 전용 MCP 서버
"""

import sqlite3
import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, List, Any, Optional

class ChatGPTMCPServer:
    def __init__(self, database_path: str):
        self.database_path = database_path
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
    
    def setup_routes(self):
        """Flask 라우트 설정"""
        
        @self.app.route('/.well-known/mcp/config', methods=['GET'])
        def mcp_config():
            """MCP 설정 정보"""
            return jsonify({
                "version": "1.0",
                "name": "Bird Collision SQLite MCP Server",
                "description": "SQLite database for bird collision data analysis",
                "capabilities": {
                    "tools": True,
                    "resources": False,
                    "prompts": False
                },
                "auth": {
                    "type": "none"
                }
            })
        
        @self.app.route('/mcp/tools', methods=['GET'])
        def list_tools():
            """도구 목록"""
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
                    },
                    {
                        "name": "get_sample_queries",
                        "description": "Get sample queries for common analysis",
                        "inputSchema": {
                            "type": "object", 
                            "properties": {}
                        }
                    }
                ]
            })
        
        @self.app.route('/mcp/tools/call', methods=['POST'])
        def call_tool():
            """도구 호출"""
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            tool_name = data.get("name")
            tool_params = data.get("arguments", {})
            
            if tool_name == "execute_sql":
                query = tool_params.get("query")
                result = self.execute_query(query)
                
                return jsonify({
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2, default=str)
                        }
                    ]
                })
            
            elif tool_name == "get_schema":
                result = self.get_schema()
                return jsonify({
                    "content": [
                        {
                            "type": "text", 
                            "text": json.dumps(result, ensure_ascii=False, indent=2, default=str)
                        }
                    ]
                })
            
            elif tool_name == "get_sample_queries":
                result = self.get_sample_queries()
                return jsonify({
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2, default=str)
                        }
                    ]
                })
            
            return jsonify({"error": "Unknown tool"}), 400
        
        @self.app.route('/backend-api/aip/connectors/mcp/oauth_config', methods=['GET'])
        def oauth_config():
            """OAuth 설정 (ChatGPT Desktop 호환)"""
            return jsonify({
                "auth_type": "none",
                "client_id": None,
                "authorization_url": None,
                "token_url": None,
                "scope": None
            })
        
        @self.app.route('/mcp/initialize', methods=['POST'])
        def initialize():
            """MCP 초기화"""
            return jsonify({
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "Bird Collision SQLite MCP Server",
                    "version": "1.0.0"
                }
            })
        
        @self.app.route('/mcp/ping', methods=['GET'])
        def ping():
            """MCP Ping"""
            return jsonify({"result": "pong"})
        
        @self.app.route('/mcp/notifications/initialized', methods=['POST'])
        def notifications_initialized():
            """MCP 초기화 완료 알림"""
            return jsonify({"result": {}})
        
        @self.app.route('/', methods=['GET', 'POST'])
        def root():
            """루트 엔드포인트 - MCP 요청 처리"""
            if request.method == 'POST':
                # JSON-RPC over HTTP 처리
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400
                
                method = data.get("method")
                params = data.get("params", {})
                request_id = data.get("id")
                
                try:
                    if method == "initialize":
                        result = {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "Bird Collision SQLite MCP Server",
                                "version": "1.0.0"
                            }
                        }
                    elif method == "tools/list":
                        result = self.handle_tools_list(params)
                    elif method == "tools/call":
                        result = self.handle_tools_call(params)
                    elif method == "notifications/initialized":
                        result = {}
                    else:
                        raise Exception(f"Unknown method: {method}")
                    
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    })
                    
                except Exception as e:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        }
                    })
            
            else:
                # GET 요청
                return jsonify({
                    "name": "Bird Collision SQLite MCP Server",
                    "version": "1.0.0",
                    "description": "MCP server for bird collision database analysis",
                    "endpoints": {
                        "health": "/health",
                        "mcp_config": "/.well-known/mcp/config",
                        "tools": "/mcp/tools",
                        "oauth_config": "/backend-api/aip/connectors/mcp/oauth_config"
                    }
                })
        
        def handle_tools_list(self, params):
            """도구 목록 반환"""
            return {
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
            }
        
        def handle_tools_call(self, params):
            """도구 호출 처리"""
            tool_name = params.get("name")
            tool_arguments = params.get("arguments", {})
            
            if tool_name == "execute_sql":
                query = tool_arguments.get("query")
                result = self.execute_query(query)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2, default=str)
                        }
                    ]
                }
            
            elif tool_name == "get_schema":
                result = self.get_schema()
                return {
                    "content": [
                        {
                            "type": "text", 
                            "text": json.dumps(result, ensure_ascii=False, indent=2, default=str)
                        }
                    ]
                }
            
            else:
                raise Exception(f"Unknown tool: {tool_name}")
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                "status": "healthy", 
                "database": os.path.exists(self.database_path),
                "mcp_version": "1.0"
            })
    
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
                "views": views,
                "description": "Bird collision database with incident data from 2023-2024"
            }
            
            return {"success": True, "schema": schema}
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()
    
    def get_sample_queries(self) -> Dict[str, Any]:
        """샘플 쿼리 제공"""
        queries = {
            "basic_stats": {
                "description": "전체 통계",
                "query": "SELECT COUNT(*) as total_incidents, COUNT(DISTINCT korean_name) as species_count, COUNT(DISTINCT province) as province_count FROM bird_collisions;"
            },
            "top_species": {
                "description": "위험한 조류 종 TOP 10",
                "query": "SELECT korean_name, incident_count, total_individuals FROM species_statistics LIMIT 10;"
            },
            "province_stats": {
                "description": "지역별 사고 현황",
                "query": "SELECT province, total_incidents, species_count FROM province_statistics ORDER BY total_incidents DESC;"
            },
            "monthly_trends": {
                "description": "월별 트렌드",
                "query": "SELECT year, month, incidents, species_count FROM monthly_trends ORDER BY year, month;"
            },
            "seasonal_analysis": {
                "description": "계절별 분석",
                "query": "SELECT season, incidents, species_count FROM seasonal_analysis ORDER BY incidents DESC;"
            }
        }
        
        return {"success": True, "sample_queries": queries}

def main():
    """메인 함수"""
    database_path = os.environ.get("DATABASE_PATH", "/Users/suntaekim/nie/bird_collision_mcp.db")
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "127.0.0.1")
    
    if not os.path.exists(database_path):
        print(f"❌ Database file not found: {database_path}")
        return
    
    server = ChatGPTMCPServer(database_path)
    
    print(f"🚀 ChatGPT MCP Server starting...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"💾 Database: {database_path}")
    print(f"🔗 Health Check: http://{host}:{port}/health")
    print(f"📋 MCP Config: http://{host}:{port}/.well-known/mcp/config")
    print(f"🛠️  Tools: http://{host}:{port}/mcp/tools")
    
    server.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    main()