class SchemaParser:
    """Schema解析器 - 负责解析GraphQL schema"""
    
    def extract_queries(self, schema):
        """从schema中提取所有查询定义"""
        queries = []
        
        if not schema:
            return queries
        
        try:
            # 检查是否有错误信息
            if 'errors' in schema:
                print(f"Schema contains errors: {schema['errors']}")
                return queries
            
            types = schema.get('data', {}).get('__schema', {}).get('types', [])
            for type_obj in types:
                if type_obj.get('name') == 'Query':
                    fields = type_obj.get('fields', [])
                    for field in fields:
                        query_name = field.get('name')
                        if query_name:
                            queries.append({
                                'name': query_name,
                                'args': field.get('args', []),
                                'type': field.get('type', {})
                            })
                    break
        except Exception as e:
            print(f"Extract queries error: {str(e)}")
        
        return queries
    
    def get_query_type(self, query_info):
        """获取查询类型信息"""
        return {
            'name': query_info['name'],
            'args_count': len(query_info['args']),
            'type_kind': query_info['type'].get('kind', 'UNKNOWN')
        }