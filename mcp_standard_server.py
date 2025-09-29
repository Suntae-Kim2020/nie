#!/usr/bin/env python3
"""
표준 MCP 서버 (JSON-RPC over stdio)
ChatGPT Desktop 호환용 조류충돌 데이터베이스 MCP 서버
"""

import sqlite3
import json
import sys
import os
from typing import Dict, List, Any, Optional

class StandardMCPServer:
    def __init__(self, database_path: str):
        self.database_path = database_path
        
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
            return {"error": str(e)}
        finally:
            conn.close()
    
    def get_sample_queries(self) -> Dict[str, Any]:
        """샘플 쿼리 제공"""
        queries = {
            "basic_stats": {
                "description": "전체 통계",
                "query": "SELECT COUNT(*) as total_incidents, COUNT(DISTINCT korean_name) as species_count FROM bird_collisions;"
            },
            "top_species": {
                "description": "위험한 조류 종 TOP 10",
                "query": "SELECT korean_name, incident_count, total_individuals FROM species_statistics LIMIT 10;"
            },
            "province_stats": {
                "description": "지역별 사고 현황",
                "query": "SELECT province, total_incidents, species_count FROM province_statistics ORDER BY total_incidents DESC;"
            }
        }
        
        return {"success": True, "sample_queries": queries}
    
    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 초기화"""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "Bird Collision SQLite MCP Server",
                "version": "1.0.0"
            }
        }
    
    def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """도구 목록"""
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
        }
    
    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """도구 호출"""
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
        
        elif tool_name == "get_sample_queries":
            result = self.get_sample_queries()
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
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """JSON-RPC 요청 처리"""
        method = request.get("method")
        params = request.get("params", {})
        
        try:
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "tools/list":
                result = self.handle_tools_list(params)
            elif method == "tools/call":
                result = self.handle_tools_call(params)
            elif method == "notifications/initialized":
                result = {}
            else:
                raise Exception(f"Unknown method: {method}")
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    def run(self):
        """MCP 서버 실행 (stdin/stdout)"""
        if not os.path.exists(self.database_path):
            print(f"Database file not found: {self.database_path}", file=sys.stderr)
            sys.exit(1)
        
        print("Bird Collision SQLite MCP Server started", file=sys.stderr)
        print(f"Database: {self.database_path}", file=sys.stderr)
        
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {e}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {e}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

def main():
    """메인 함수"""
    database_path = os.environ.get("DATABASE_PATH", "/Users/suntaekim/nie/bird_collision_mcp.db")
    
    server = StandardMCPServer(database_path)
    server.run()

if __name__ == "__main__":
    main()