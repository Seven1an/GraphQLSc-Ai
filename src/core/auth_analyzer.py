class AuthAnalyzer:
    """授权分析器 - 负责分析授权状态"""
    
    def analyze_response(self, response_data):
        """分析响应数据，判断授权状态 - 二极管匹配逻辑"""
        if 'errors' in response_data:
            errors = response_data['errors']
            
            # 检查是否有授权错误 - 只检查是否包含 "authorized"
            has_auth_error = False
            for error in errors:
                error_message = error.get('message', '').lower()
                
                # 二极管匹配：只要包含 "authorized" 就认为是授权错误
                if 'authorized' in error_message:
                    has_auth_error = True
                    break
            
            if has_auth_error:
                return 'auth_required'
            else:
                # 其他所有情况都放到 auth_ok
                return 'auth_ok'
        
        # 没有错误，授权OK
        return 'auth_ok'
    
    def get_error_details(self, response_data):
        """获取错误详情"""
        if 'errors' not in response_data:
            return []
        
        errors = []
        for error in response_data['errors']:
            error_info = {
                'message': error.get('message', ''),
                'locations': error.get('locations', []),
                'path': error.get('path', [])
            }
            errors.append(error_info)
        
        return errors