import os
import json

class FileManager:
    """文件管理器 - 负责所有文件操作"""
    
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
    
    def ensure_directory(self, directory):
        """确保目录存在"""
        full_path = os.path.join(self.base_dir, directory)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        return full_path
    
    def write_text(self, filepath, content):
        """写入文本文件"""
        try:
            # 确保目录存在
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Write file error: {str(e)}")
            return False
    
    def exists(self, path):
        """检查文件或目录是否存在"""
        return os.path.exists(path)
    
    def create_directory(self, directory):
        """创建目录"""
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                return True
            return True
        except Exception as e:
            print(f"Create directory error: {str(e)}")
            return False
    
    def write_json(self, filepath, data):
        """写入JSON文件"""
        try:
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Write JSON error: {str(e)}")
            return False
    
    def read_json(self, filepath):
        """读取JSON文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Read JSON error: {str(e)}")
            return None