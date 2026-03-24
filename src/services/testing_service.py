import time
from ..network.http_client import HTTPClient
from ..core.query_builder import QueryBuilder
from ..core.auth_analyzer import AuthAnalyzer

class TestingService:
    """测试服务 - 负责执行GraphQL查询测试"""
    
    def __init__(self):
        self.http_client = HTTPClient()
        self.query_builder = QueryBuilder()
        self.auth_analyzer = AuthAnalyzer()
    
    def test_query(self, endpoint, query_info):
        """测试单个查询"""
        query_name = query_info['name']
        
        try:
            # 生成查询
            query = self.query_builder.generate_query(query_info)
            
            # 发送请求
            payload = {'query': query}
            result = self.http_client.post(endpoint, payload)
            
            if result['success']:
                response = result['response']
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        
                        # 分析授权状态
                        auth_status = self.auth_analyzer.analyze_response(response_data)
                        
                        return {
                            'status': auth_status,
                            'query_name': query_name,
                            'query': query,
                            'response_data': response_data,
                            'response_time': result['response_time']
                        }
                    except Exception as e:
                        return {
                            'status': 'error',
                            'query_name': query_name,
                            'error': f'Parse response error: {str(e)}',
                            'response_time': result['response_time']
                        }
                else:
                    return {
                        'status': 'error',
                        'query_name': query_name,
                        'error': f'HTTP Error: {response.status_code}',
                        'response_time': result['response_time']
                    }
            else:
                return {
                    'status': 'error',
                    'query_name': query_name,
                    'error': result['error'],
                    'response_time': result['response_time']
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'query_name': query_name,
                'error': f'Test error: {str(e)}',
                'response_time': 0
            }
    
    def execute_query(self, endpoint, query_data):
        """执行单个GraphQL查询（用于AI工作流）"""
        try:
            result = self.http_client.post(endpoint, query_data)
            
            if result['success']:
                response = result['response']
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except Exception as e:
                        return {'error': f'Parse error: {str(e)}'}
                else:
                    return {'error': f'HTTP Error: {response.status_code}'}
            else:
                return {'error': result['error']}
                
        except Exception as e:
            return {'error': f'Request error: {str(e)}'}
    
    def batch_test(self, endpoint, queries, delay=0.5, result_service=None):
        """批量测试查询 - 流式写入"""
        results = {
            'auth_ok': [],        # 真正成功的接口
            'auth_required': [],  # 包含authorized的接口
            'other': [],          # 其他错误接口
            'errors': []          # 网络/解析错误
        }
        
        for i, query_info in enumerate(queries, 1):
            result = self.test_query(endpoint, query_info)
            
            # 流式写入：立即写入文件
            if result_service:
                result_service.append_result(endpoint, result)
            
            # 同时保持内存中的统计（用于最终统计）
            if result['status'] == 'auth_ok':
                # 检查是否真正成功（没有错误信息）
                if 'errors' not in result['response_data']:
                    results['auth_ok'].append(result)
                    print(f"[{i}/{len(queries)}] Success: {result['query_name']}")
                else:
                    # 有错误但不是授权错误，放到other
                    results['other'].append(result)
                    print(f"[{i}/{len(queries)}] Other Error: {result['query_name']}")
            elif result['status'] == 'auth_required':
                results['auth_required'].append(result)
                print(f"[{i}/{len(queries)}] Auth Required: {result['query_name']}")
            else:
                results['errors'].append(result)
                print(f"[{i}/{len(queries)}] Error: {result['query_name']} - {result['error']}")
            
            # 避免请求过于频繁
            time.sleep(delay)
        
        return results
