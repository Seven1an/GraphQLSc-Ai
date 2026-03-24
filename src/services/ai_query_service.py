#!/usr/bin/env python3
"""
AI Query Generation Service
AI驱动的GraphQL查询生成服务
"""

import json
import requests
import os
import sys
from typing import Dict, List, Optional

# Add config to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import load_config


class AIQueryService:
    """AI驱动的GraphQL查询生成服务"""
    
    def __init__(self):
        """初始化服务"""
        self.config = load_config()
        self.messages: List[Dict[str, str]] = []
        self._init_system_prompt()
    
    def _init_system_prompt(self):
        """初始化系统提示词"""
        system_prompt = """你是一个 GraphQL 自动化枚举专家。用户会提供 GraphQL 请求及其响应结果，你需要基于当前响应，生成下一步唯一正确的 GraphQL 查询语句，逐步递归，直到获取完整数据结构。
 
规则：
 
只返回 GraphQL 语句，禁止输出任何解释或额外内容。
 
流程规范：
 
起点阶段
通过已有查询获取 __typename，用于确定当前对象类型。
类型解析阶段
一旦获得 __typename，必须立即发起标准内省查询，获取完整字段结构，禁止只查询字段名。

固定使用如下结构：

{
  "query": "query GetTypeFields($typeName: String!) { __type(name: $typeName) { fields { name type { kind name ofType { kind name ofType { kind name } } } } } }",
  "variables": {
    "typeName": "类型名"
  }
}

类型结构解析规则
必须解析 type.kind、type.name、type.ofType（递归）以还原真实类型：
SCALAR / ENUM → 标量，可直接查询
OBJECT → 非标量，必须添加子选择集
LIST / NON_NULL → 继续展开 ofType 直到拿到真实类型
查询构造规则
所有标量字段必须加入查询
所有非标量字段必须包含子字段选择集
子字段来源必须通过对应类型的 __type 再次内省获取
严禁对 OBJECT 类型字段直接查询而不加子选择
递归策略

当响应中出现：

__typename 为新对象类型
或字段类型为 OBJECT

必须对该类型重复执行：
内省 → 获取字段 → 构造子查询

错误修正机制

若返回错误包含：
"must have a selection of subfields" 或类似提示

说明存在未展开的 OBJECT 字段，必须补充该字段的子选择集。

终止条件

当查询：

无错误返回
所有字段已完整展开
不再出现新的 OBJECT 类型未解析
查询到了具体参数的值

此时你通过输出OK来终止本接口的查询

流程结束。

核心执行链路：

__typename → __type（完整结构）→ 解析类型 → 构造查询 → 发现 OBJECT → 递归内省 → 补全子字段 → 直到结构完全展开"""
        
        self.messages.append({"role": "system", "content": system_prompt})
    
    def call_deepseek(self) -> str:
        """调用 AI API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.get('ai_provider', 'api_key')}"
        }
        
        data = {
            "model": self.config.get('ai_provider', 'model'),
            "messages": self.messages,
            "max_tokens": self.config.getint('ai_provider', 'max_tokens'),
            "temperature": self.config.getfloat('ai_provider', 'temperature')
        }
        
        try:
            response = requests.post(
                self.config.get('ai_provider', 'api_url'), 
                headers=headers, 
                json=data, 
                timeout=self.config.getint('ai_provider', 'request_timeout')
            )
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def should_stop(self, ai_response: str) -> bool:
        """检查AI是否输出OK终止"""
        return ai_response.strip().upper() == "OK"
    
    def add_user_message(self, query_data: Dict, response: Dict):
        """添加用户消息到对话历史"""
        user_prompt = f"""发送了: {json.dumps(query_data, ensure_ascii=False)}

返回了: {json.dumps(response, ensure_ascii=False)}

请根据响应结果，生成下一个要发送的GraphQL查询语句。"""
        
        self.messages.append({"role": "user", "content": user_prompt})
    
    def get_ai_response(self) -> str:
        """获取AI响应并添加到历史"""
        ai_response = self.call_deepseek()
        self.messages.append({"role": "assistant", "content": ai_response})
        return ai_response
    
    def parse_ai_response(self, ai_response: str) -> Optional[Dict]:
        """解析AI响应为JSON"""
        try:
            return json.loads(ai_response)
        except:
            return None
    
    def reset(self):
        """重置对话历史"""
        self.messages = []
        self._init_system_prompt()
