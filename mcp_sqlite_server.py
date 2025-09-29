#!/usr/bin/env python3
"""
SQLite MCP Server for ChatGPT Desktop
조류충돌 데이터베이스에 대한 MCP 서버 구현
"""

import sqlite3
import json
import sys
import os
from typing import Dict, List, Any, Optional

class SQLiteMCPServer:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.conn = None
        
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.conn = sqlite3.connect(self.database_path)
            self.conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
            return True
        except Exception as e:
            print(f"Database connection failed: {e}", file=sys.stderr)
            return False
    
    def execute_query(self, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        """쿼리 실행"""
        if not self.conn:
            if not self.connect():
                return {"error": "Database connection failed"}
        
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # SELECT 쿼리인지 확인
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                # Row 객체를 딕셔너리로 변환
                data = [dict(row) for row in results]
                return {
                    "success": True,
                    "data": data,
                    "row_count": len(data)
                }
            else:
                # INSERT, UPDATE, DELETE 등
                self.conn.commit()
                return {
                    "success": True,
                    "affected_rows": cursor.rowcount
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    def get_schema(self) -> Dict[str, Any]:
        """데이터베이스 스키마 정보"""
        try:
            # 테이블 목록
            tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables_result = self.execute_query(tables_query)
            
            # 뷰 목록
            views_query = "SELECT name FROM sqlite_master WHERE type='view'"
            views_result = self.execute_query(views_query)
            
            schema = {
                "tables": tables_result.get("data", []),
                "views": views_result.get("data", [])
            }
            
            # 각 테이블의 컬럼 정보
            for table in schema["tables"]:
                table_name = table["name"]
                columns_query = f"PRAGMA table_info({table_name})"
                columns_result = self.execute_query(columns_query)
                schema[f"{table_name}_columns"] = columns_result.get("data", [])
            
            return {"success": True, "schema": schema}
            
        except Exception as e:
            return {"error": str(e)}
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 요청 처리"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
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
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_params = params.get("arguments", {})
            
            if tool_name == "execute_sql":
                query = tool_params.get("query")
                query_params = tool_params.get("params")
                result = self.execute_query(query, query_params)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            
            elif tool_name == "get_schema":
                result = self.get_schema()
                return {
                    "content": [
                        {
                            "type": "text", 
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
        
        return {"error": "Unknown method or tool"}
    
    def run(self):
        """MCP 서버 실행"""
        if not self.connect():
            sys.exit(1)
        
        # 표준 입력에서 JSON-RPC 메시지 읽기
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = self.handle_request(request)
                
                # 응답에 ID 추가 (JSON-RPC 규격)
                if "id" in request:
                    response["id"] = request["id"]
                
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError:
                error_response = {
                    "error": {"code": -32700, "message": "Parse error"}
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
            except Exception as e:
                error_response = {
                    "error": {"code": -32603, "message": f"Internal error: {e}"}
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

def main():
    """메인 함수"""
    database_path = os.environ.get("DATABASE_PATH", "bird_collision_mcp.db")
    
    if not os.path.exists(database_path):
        print(f"Database file not found: {database_path}", file=sys.stderr)
        sys.exit(1)
    
    server = SQLiteMCPServer(database_path)
    server.run()

if __name__ == "__main__":
    main()