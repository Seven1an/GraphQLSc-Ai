from ..network.http_client import HTTPClient
from ..core.schema_parser import SchemaParser
from ..storage.file_manager import FileManager

class SchemaService:
    """Schema服务 - 负责获取和处理GraphQL schema"""
    
    def __init__(self):
        self.http_client = HTTPClient()
        self.schema_parser = SchemaParser()
        self.file_manager = FileManager()
        
        # 完整的Introspection查询
        self.introspection_query = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              ...FullType
            }
            directives {
              name
              description
              locations
              args {
                ...InputValue
              }
            }
          }
        }

        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
          }
          possibleTypes {
            ...TypeRef
          }
        }

        fragment InputValue on __InputValue {
          name
          description
          type { ...TypeRef }
          defaultValue
        }

        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
    
    def fetch_schema(self, endpoint):
        """获取GraphQL schema并保存到文件"""
        # 确保 URL 以 /graphql 结尾
        url = self._normalize_url(endpoint)
        
        payload = {
            "query": self.introspection_query,
            "variables": {},
            "operationName": "IntrospectionQuery"
        }
        
        result = self.http_client.post(url, payload)
        
        if result['success']:
            response = result['response']
            if response.status_code == 200:
                try:
                    schema_data = response.json()
                    
                    # 保存schema到IntrospectionQuery目录
                    self._save_schema_to_file(schema_data, endpoint)
                    
                    return schema_data
                except Exception as e:
                    print(f"Parse response error: {str(e)}")
            else:
                print(f"HTTP Error: {response.status_code}")
        else:
            print(f"Request error: {result['error']}")
        
        return None
    
    def _save_schema_to_file(self, schema_data, endpoint):
        """保存schema数据到IntrospectionQuery目录"""
        import json
        
        # 确保IntrospectionQuery目录存在
        directory = "IntrospectionQuery"
        if not self.file_manager.exists(directory):
            self.file_manager.create_directory(directory)
        
        # 使用标准化文件名
        filename = self._generate_filename(endpoint)
        filepath = f"{directory}/{filename}_GraphQL.json"
        
        try:
            # 格式化JSON输出
            formatted_json = json.dumps(schema_data, indent=2, ensure_ascii=False)
            
            if self.file_manager.write_text(filepath, formatted_json):
                print(f"Schema saved to: {filepath}")
            else:
                print("Failed to save schema file")
        except Exception as e:
            print(f"Save schema error: {str(e)}")
    
    def extract_queries(self, schema):
        """从schema中提取查询"""
        return self.schema_parser.extract_queries(schema)
    
    def _generate_filename(self, url):
        """根据URL生成标准化文件名"""
        # 移除协议部分
        filename = url.replace('http://', '').replace('https://', '')
        # 替换特殊字符为下划线，确保文件名有效
        filename = filename.replace('/', '_').replace(':', '_').replace('.', '_')
        return filename
    
    def _normalize_url(self, url):
        """标准化URL"""
        if not url.endswith('/graphql'):
            if url.endswith('/'):
                url += 'graphql'
            else:
                url += '/graphql'
        return url