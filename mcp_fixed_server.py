#!/usr/bin/env python3
"""
ChatGPT Desktop 완전 호환 MCP 서버
모든 요청을 로깅하고 정확한 MCP 프로토콜 구현
"""

import sqlite3
import json
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, List, Any, Optional
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPFixedServer:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.app = Flask(__name__)
        CORS(self.app, origins="*", methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])
        self.setup_routes()
        
    def connect_db(self):
        """데이터베이스 연결"""
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
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
            logger.error(f"Query execution failed: {e}")
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
            
            return {
                "success": True,
                "schema": {
                    "tables": tables,
                    "views": views,
                    "description": "Bird collision database with incident data from 2023-2024"
                }
            }
            
        except Exception as e:
            logger.error(f"Schema retrieval failed: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    def setup_routes(self):
        """Flask 라우트 설정"""
        
        @self.app.before_request
        def log_request():
            """모든 요청 로깅"""
            logger.info(f"=== REQUEST ===")
            logger.info(f"Method: {request.method}")
            logger.info(f"URL: {request.url}")
            logger.info(f"Path: {request.path}")
            logger.info(f"Headers: {dict(request.headers)}")
            if request.method in ['POST', 'PUT', 'PATCH']:
                logger.info(f"Data: {request.get_data(as_text=True)}")
        
        @self.app.after_request
        def log_response(response):
            """모든 응답 로깅"""
            logger.info(f"=== RESPONSE ===")
            logger.info(f"Status: {response.status}")
            logger.info(f"Headers: {dict(response.headers)}")
            if response.content_type and 'json' in response.content_type:
                logger.info(f"Body: {response.get_data(as_text=True)}")
            logger.info(f"================")
            return response
        
        @self.app.route('/.well-known/mcp/config', methods=['GET'])
        def mcp_config():
            """MCP 설정 정보 (표준)"""
            config = {
                "version": "2024-11-05",
                "name": "Bird Collision SQLite MCP Server",
                "description": "SQLite database for bird collision data analysis",
                "capabilities": {
                    "tools": True,
                    "resources": False,
                    "prompts": False
                },
                "serverInfo": {
                    "name": "Bird Collision SQLite MCP Server",
                    "version": "1.0.0"
                }
            }
            logger.info(f"Returning MCP config: {config}")
            return jsonify(config)
        
        @self.app.route('/mcp/server-info', methods=['GET'])
        def server_info():
            """서버 정보"""
            info = {
                "name": "Bird Collision SQLite MCP Server",
                "version": "1.0.0",
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                }
            }
            return jsonify(info)
        
        @self.app.route('/mcp/initialize', methods=['POST'])
        def initialize():
            """MCP 초기화"""
            data = request.get_json() or {}
            logger.info(f"Initialize request: {data}")
            
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
            return jsonify(result)
        
        @self.app.route('/mcp/tools', methods=['GET'])
        def list_tools():
            """도구 목록"""
            tools = {
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
            return jsonify(tools)
        
        @self.app.route('/mcp/tools/call', methods=['POST'])
        def call_tool():
            """도구 호출"""
            data = request.get_json()
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
            
            logger.info(f"Tool call request: {data}")
            
            tool_name = data.get("name")
            tool_arguments = data.get("arguments", {})
            
            try:
                if tool_name == "execute_sql":
                    query = tool_arguments.get("query")
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
                
                else:
                    return jsonify({"error": f"Unknown tool: {tool_name}"}), 400
                    
            except Exception as e:
                logger.error(f"Tool call failed: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/', methods=['GET', 'POST', 'OPTIONS'])
        def root():
            """루트 엔드포인트 - 모든 MCP 요청 처리"""
            if request.method == 'OPTIONS':
                return '', 204
                
            if request.method == 'POST':
                # JSON-RPC over HTTP 처리
                data = request.get_json()
                if not data:
                    logger.error("No JSON data in POST request")
                    return jsonify({"error": "No JSON data provided"}), 400
                
                logger.info(f"JSON-RPC request: {data}")
                
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
                        result = {
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
                    elif method == "tools/call":
                        tool_name = params.get("name")
                        tool_arguments = params.get("arguments", {})
                        
                        if tool_name == "execute_sql":
                            query = tool_arguments.get("query")
                            query_result = self.execute_query(query)
                            result = {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(query_result, ensure_ascii=False, indent=2, default=str)
                                    }
                                ]
                            }
                        elif tool_name == "get_schema":
                            schema_result = self.get_schema()
                            result = {
                                "content": [
                                    {
                                        "type": "text", 
                                        "text": json.dumps(schema_result, ensure_ascii=False, indent=2, default=str)
                                    }
                                ]
                            }
                        else:
                            raise Exception(f"Unknown tool: {tool_name}")
                            
                    elif method == "notifications/initialized":
                        result = {}
                    else:
                        raise Exception(f"Unknown method: {method}")
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    }
                    logger.info(f"JSON-RPC response: {response}")
                    return jsonify(response)
                    
                except Exception as e:
                    logger.error(f"JSON-RPC error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": str(e)
                        }
                    }
                    return jsonify(error_response), 500
            
            else:
                # GET 요청
                return jsonify({
                    "name": "Bird Collision SQLite MCP Server",
                    "version": "1.0.0",
                    "description": "MCP server for bird collision database analysis",
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": True,
                        "resources": False,
                        "prompts": False
                    },
                    "endpoints": {
                        "health": "/health",
                        "mcp_config": "/.well-known/mcp/config",
                        "tools": "/mcp/tools",
                        "server_info": "/mcp/server-info"
                    }
                })
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({
                "status": "healthy", 
                "database": os.path.exists(self.database_path),
                "mcp_version": "2024-11-05",
                "timestamp": datetime.now().isoformat()
            })

def main():
    """메인 함수"""
    database_path = os.environ.get("DATABASE_PATH", "/Users/suntaekim/nie/bird_collision_mcp.db")
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "127.0.0.1")
    
    if not os.path.exists(database_path):
        logger.error(f"Database file not found: {database_path}")
        return
    
    server = MCPFixedServer(database_path)
    
    logger.info(f"🚀 MCP Fixed Server starting...")
    logger.info(f"📍 URL: http://{host}:{port}")
    logger.info(f"💾 Database: {database_path}")
    logger.info(f"🔗 Health Check: http://{host}:{port}/health")
    logger.info(f"📋 MCP Config: http://{host}:{port}/.well-known/mcp/config")
    logger.info(f"🛠️  Tools: http://{host}:{port}/mcp/tools")
    
    server.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    main()