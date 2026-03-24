from ..storage.file_manager import FileManager
import os

class ResultService:
    """结果服务 - 负责处理测试结果"""
    
    def __init__(self, output_dir="requestfortest"):
        self.file_manager = FileManager()
        self.output_dir = output_dir
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def save_test_results(self, endpoint, test_results):
        """保存测试结果 - 三文件分类"""
        filename = self._generate_filename(endpoint)
        
        # 保存真正成功的结果
        if test_results['auth_ok']:
            self._save_auth_ok_results(filename, test_results['auth_ok'])
        
        # 保存需要授权的结果
        if test_results['auth_required']:
            self._save_auth_required_results(filename, test_results['auth_required'])
        
        # 保存其他错误结果
        if test_results['other']:
            self._save_other_results(filename, test_results['other'])
        
        # 保存网络/解析错误结果
        if test_results['errors']:
            self._save_error_results(filename, test_results['errors'])
    
    def _generate_filename(self, url):
        """根据URL生成文件名"""
        # 移除协议部分
        filename = url.replace('http://', '').replace('https://', '')
        # 替换特殊字符为下划线，确保文件名有效
        filename = filename.replace('/', '_').replace(':', '_').replace('.', '_')
        return filename
    
    def _save_auth_ok_results(self, filename, results):
        """保存授权OK的结果 - 英文格式"""
        content = f"Auth OK Queries ({len(results)} queries)\n"
        content += "=" * 50 + "\n\n"
        
        for result in results:
            content += f"Query Name: {result['query_name']}\n"
            
            # 如果有错误信息，显示错误
            if 'errors' in result['response_data']:
                errors = result['response_data']['errors']
                content += f"Errors: {errors}\n"
            else:
                content += "Response Status: Success\n"
            
            content += "-" * 30 + "\n\n"
        
        filepath = f"{self.output_dir}/{filename}_auth_ok.txt"
        if self.file_manager.write_text(filepath, content):
            print(f"Auth OK results saved to: {filepath}")
    
    def _save_auth_required_results(self, filename, results):
        """保存需要授权的结果 - 英文格式"""
        content = f"Auth Required Queries ({len(results)} queries)\n"
        content += "=" * 50 + "\n\n"
        
        for result in results:
            content += f"Query Name: {result['query_name']}\n"
            
            # 只显示授权相关的错误信息
            if 'errors' in result['response_data']:
                errors = result['response_data']['errors']
                content += f"Authorization Errors: {errors}\n"
            
            content += "-" * 30 + "\n\n"
        
        filepath = f"{self.output_dir}/{filename}_auth_required.txt"
        if self.file_manager.write_text(filepath, content):
            print(f"Auth required results saved to: {filepath}")
    
    def _save_other_results(self, filename, results):
        """保存其他错误结果 - 英文格式"""
        content = f"Other Error Queries ({len(results)} queries)\n"
        content += "=" * 50 + "\n\n"
        
        for result in results:
            content += f"Query Name: {result['query_name']}\n"
            
            # 显示错误信息
            if 'errors' in result['response_data']:
                errors = result['response_data']['errors']
                content += f"Errors: {errors}\n"
            
            content += "-" * 30 + "\n\n"
        
        filepath = f"{self.output_dir}/{filename}_other.txt"
        if self.file_manager.write_text(filepath, content):
            print(f"Other error results saved to: {filepath}")
    
    def _save_error_results(self, filename, results):
        """保存错误结果 - 英文格式"""
        content = f"Error Queries ({len(results)} queries)\n"
        content += "=" * 50 + "\n\n"
        
        for result in results:
            content += f"Query Name: {result['query_name']}\n"
            content += f"Error: {result.get('error', 'Unknown error')}\n"
            content += "-" * 30 + "\n\n"
        
        filepath = f"{self.output_dir}/{filename}_errors.txt"
        if self.file_manager.write_text(filepath, content):
            print(f"Error results saved to: {filepath}")
    
    def append_result(self, endpoint, result):
        """流式写入单个测试结果"""
        filename = self._generate_filename(endpoint)
        
        # 根据结果状态确定文件类型
        if result['status'] == 'auth_ok':
            if 'errors' not in result['response_data']:
                file_type = 'auth_ok'
            else:
                file_type = 'other'
        elif result['status'] == 'auth_required':
            file_type = 'auth_required'
        else:
            file_type = 'errors'
        
        # 构建文件内容
        content = self._format_result_content(result, file_type)
        
        # 追加写入文件
        filepath = f"{self.output_dir}/{filename}_{file_type}.txt"
        
        try:
            # 如果是第一次写入，添加文件头部
            if not os.path.exists(filepath):
                header = self._get_file_header(file_type)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(header)
            
            # 追加内容
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Append result error: {str(e)}")
    
    def _format_result_content(self, result, file_type):
        """格式化单个结果的内容"""
        content = f"Query Name: {result['query_name']}\n"
        
        if file_type == 'auth_ok':
            content += "Response Status: Success\n"
        elif file_type == 'auth_required':
            if 'errors' in result['response_data']:
                errors = result['response_data']['errors']
                content += f"Authorization Errors: {errors}\n"
        elif file_type == 'other':
            if 'errors' in result['response_data']:
                errors = result['response_data']['errors']
                content += f"Errors: {errors}\n"
        else:  # errors
            content += f"Error: {result.get('error', 'Unknown error')}\n"
        
        content += "-" * 30 + "\n\n"
        return content
    
    def _get_file_header(self, file_type):
        """获取文件头部信息"""
        headers = {
            'auth_ok': "Auth OK Queries\n" + "=" * 50 + "\n\n",
            'auth_required': "Auth Required Queries\n" + "=" * 50 + "\n\n",
            'other': "Other Error Queries\n" + "=" * 50 + "\n\n",
            'errors': "Error Queries\n" + "=" * 50 + "\n\n"
        }
        return headers.get(file_type, "")
    
    def get_statistics(self, test_results):
        """获取统计信息"""
        return {
            'total': len(test_results['auth_ok']) + len(test_results['auth_required']) + len(test_results['other']) + len(test_results['errors']),
            'auth_ok': len(test_results['auth_ok']),
            'auth_required': len(test_results['auth_required']),
            'other': len(test_results['other']),
            'errors': len(test_results['errors'])
        }