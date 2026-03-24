class QueryBuilder:
    """查询构建器 - 负责生成GraphQL查询"""
    
    def generate_query(self, query_info):
        """为查询生成GraphQL查询语句"""
        query_name = query_info['name']
        args = query_info['args']
        
        # 构建参数部分
        arg_str = self._build_arguments(args)
        
        # 构建查询语句，只请求基本字段
        query = f"""
        query {{
            {query_name}{arg_str} {{
                __typename
            }}
        }}
        """
        return query
    
    def _build_arguments(self, args):
        """构建参数字符串"""
        if not args:
            return ''
        
        arg_pairs = []
        for arg in args:
            arg_name = arg['name']
            # 使用默认值或简单值
            default_value = arg.get('defaultValue')
            if default_value:
                # 处理字符串类型的默认值
                if isinstance(default_value, str) and (default_value.startswith('"') or default_value.startswith("'")):
                    arg_pairs.append(f"{arg_name}: {default_value}")
                else:
                    arg_pairs.append(f"{arg_name}: {default_value}")
            else:
                # 对于必需参数，使用适当的默认值
                arg_type = arg['type']
                if arg_type.get('kind') == 'NON_NULL':
                    arg_value = self._get_default_value(arg_type)
                    if arg_value:
                        arg_pairs.append(f"{arg_name}: {arg_value}")
        
        if arg_pairs:
            return '(' + ', '.join(arg_pairs) + ')'
        return ''
    
    def _get_default_value(self, arg_type):
        """根据参数类型获取默认值"""
        of_type = arg_type.get('ofType', {})
        type_name = of_type.get('name', 'String')
        
        if type_name == 'String':
            return '\"test\"'
        elif type_name == 'Int':
            return '1'
        elif type_name == 'Boolean':
            return 'true'
        elif type_name == 'ID':
            return '\"1\"'
        return None