#!/usr/bin/env python3
"""
AI Query Generator - GraphQL API Automation Tool
"""

import json
import requests
import os
from config.settings import load_config


def call_ai_provider(messages, config):
    """Call AI Provider API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.get('ai_provider', 'api_key')}"
    }
    
    data = {
        "model": config.get('ai_provider', 'model'),
        "messages": messages,
        "max_tokens": config.getint('ai_provider', 'max_tokens'),
        "temperature": config.getfloat('ai_provider', 'temperature')
    }
    
    try:
        response = requests.post(
            config.get('ai_provider', 'api_url'),
            headers=headers,
            json=data,
            timeout=config.getint('ai_provider', 'request_timeout')
        )
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"


def execute_graphql_query(endpoint, query_data, timeout=30):
    """Execute GraphQL query"""
    try:
        response = requests.post(
            endpoint,
            json=query_data,
            headers={'Content-Type': 'application/json'},
            timeout=timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Request error: {str(e)}"}


def read_all_query_names(file_path):
    """Read all query names from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        query_names = []
        for line in lines:
            if line.startswith('Query Name:'):
                query_name = line.replace('Query Name:', '').strip()
                if query_name:
                    query_names.append(query_name)
        return query_names
    except FileNotFoundError:
        return []


def should_stop(ai_response):
    """Check if AI response indicates to stop"""
    return ai_response.strip().upper() == "OK"


def save_ok_response(endpoint, response_data):
    """Save OK response to results/ok.txt"""
    # Generate filename based on URL (same logic as requestfortest)
    filename = endpoint.replace('http://', '').replace('https://', '')
    filename = filename.replace('/', '_').replace(':', '_').replace('.', '_')
    
    # Ensure results directory exists
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    filepath = f"{results_dir}/{filename}_ok.txt"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(response_data, indent=2, ensure_ascii=False))
        print(f"OK response saved to: {filepath}")
        return True
    except Exception as e:
        print(f"Failed to save OK response: {str(e)}")
        return False


def run_ai_query_generation(endpoint, auth_ok_file, config):
    """Run AI query generation"""
    print("AI Query Generator")
    print("=" * 50)
    
    query_names = read_all_query_names(auth_ok_file)
    
    if not query_names:
        print(f"Failed to read query names from {auth_ok_file}")
        return
    
    print(f"Found {len(query_names)} queries to process\n")
    
    for idx, query_name in enumerate(query_names, 1):
        print(f"\n{'='*60}")
        print(f"Processing Query {idx}/{len(query_names)}: {query_name}")
        print(f"{'='*60}\n")
        
        messages = []
        
        system_prompt = """You are a GraphQL automation expert. The user will provide GraphQL requests and their response results. You need to generate the next correct GraphQL query based on the current response, recursively, until you get the complete data structure.
 
Rules:
 
Only return the GraphQL query, no explanations or extra content.
 
Workflow:
 
Start Phase
Get __typename from existing query to determine current object type.
Type Resolution Phase
Once you get __typename, immediately initiate a standard introspection query to get the complete field structure, do not just query field names.

Use the following structure:

{
  "query": "query GetTypeFields($typeName: String!) { __type(name: $typeName) { fields { name type { kind name ofType { kind name ofType { kind name } } } } } }",
  "variables": {
    "typeName": "TypeName"
  }
}

Type Structure Resolution Rules
Must parse type.kind, type.name, type.ofType (recursively) to restore the real type:
SCALAR / ENUM → scalar, can be queried directly
OBJECT → non-scalar, must add sub-selection set
LIST / NON_NULL → continue expanding ofType until getting the real type
Query Construction Rules
All scalar fields must be added to the query
All non-scalar fields must include sub-field selection sets
Sub-field sources must be obtained through __type introspection again for the corresponding type
Do not directly query OBJECT type fields without adding sub-selection
Recursive Strategy

When the response contains:

__typename is a new object type
or field type is OBJECT

Must repeat for this type:
Introspection → Get fields → Construct sub-query

Error Correction Mechanism

If the error contains:
"must have a selection of subfields" or similar

It means there are unexpanded OBJECT fields, must add sub-selection for that field.

Termination Condition

When the query:

No error returned
All fields are fully expanded
No new OBJECT types remain to be resolved
The specific parameter value is found

At this point, output OK to terminate this query

Workflow ends.

Core execution chain:

__typename → __type (complete structure) → Parse type → Construct query → Find OBJECT → Recursive introspection → Complete sub-fields → Until structure is fully expanded"""
        
        messages.append({"role": "system", "content": system_prompt})
        
        print(f"=== Step 1 ===")
        query_data = {"query": f"{{ {query_name} {{ __typename }} }}"}
        print(f"Sent: {json.dumps(query_data, ensure_ascii=False)}")
        
        response = execute_graphql_query(endpoint, query_data)
        print(f"Response: {json.dumps(response, ensure_ascii=False)}")
        
        if 'error' in response:
            print("Error occurred, skipping to next query.")
            continue
        
        print(f"Next step")
        
        user_prompt = f"""Sent: {json.dumps(query_data, ensure_ascii=False)}

Response: {json.dumps(response, ensure_ascii=False)}

Please generate the next GraphQL query to send based on the response."""
        
        messages.append({"role": "user", "content": user_prompt})
        ai_response = call_ai_provider(messages, config)
        print(f"AI generated: {ai_response}")
        
        messages.append({"role": "assistant", "content": ai_response})
        
        if should_stop(ai_response):
            print("\nAI query completed for this query, saving OK response...")
            save_ok_response(endpoint, response)
            continue
        
        try:
            query_data = json.loads(ai_response)
        except:
            print("Failed to parse AI response as JSON, skipping to next query.")
            continue
        
        step = 2
        while True:
            print(f"\n=== Step {step} ===")
            print(f"Sent: {json.dumps(query_data, ensure_ascii=False)}")
            
            response = execute_graphql_query(endpoint, query_data)
            print(f"Response: {json.dumps(response, ensure_ascii=False)}")
            
            if 'error' in response:
                print("\nError occurred, stopping.")
                break
            
            print(f"Next step")
            
            user_prompt = f"""Sent: {json.dumps(query_data, ensure_ascii=False)}

Response: {json.dumps(response, ensure_ascii=False)}

Please generate the next GraphQL query to send based on the response."""
            
            messages.append({"role": "user", "content": user_prompt})
            ai_response = call_ai_provider(messages, config)
            print(f"AI generated: {ai_response}")
            
            messages.append({"role": "assistant", "content": ai_response})
            
            if should_stop(ai_response):
                print("\nAI query completed for this query, saving OK response...")
                save_ok_response(endpoint, response)
                break
            
            try:
                query_data = json.loads(ai_response)
            except:
                print("Failed to parse AI response as JSON")
                break
            
            step += 1
    
    print(f"\n{'='*60}")
    print(f"All queries processed!")
    print(f"{'='*60}")
