import requests
import time

class HTTPClient:
    """HTTP客户端 - 负责所有网络请求"""
    
    def __init__(self, timeout=30):
        self.timeout = timeout
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def post(self, url, data, headers=None):
        """发送POST请求"""
        if headers is None:
            headers = self.default_headers
        
        start_time = time.time()
        try:
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'success': True,
                'response': response,
                'response_time': response_time
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': 0
            }