#!/usr/bin/env python3
"""
GraphQL API Testing Tool - Single Entry Point
Main
#Author Seven1an
"""

import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import load_config
from src.services.schema_service import SchemaService
from src.services.testing_service import TestingService
from src.services.result_service import ResultService
from ai.query_generator import run_ai_query_generation


def main():
    """Main function"""
    config = load_config()
    
    parser = argparse.ArgumentParser(
        description='GraphQL API Testing Tool - Single Entry Point'
    )
    parser.add_argument(
        '-u', '--url', 
        required=True, 
        help='GraphQL endpoint URL'
    )
    
    args = parser.parse_args()
    
    endpoint = args.url
    output_dir = config.get('graphql', 'output_dir')
    
    # Initialize services
    schema_service = SchemaService()
    testing_service = TestingService()
    result_service = ResultService(output_dir=output_dir)
    
    print("GraphQL API Testing Tool")
    print("=" * 50)
    
    # Step 1: Fetch schema
    print("\nFetching schema...")
    schema = schema_service.fetch_schema(endpoint)
    
    if not schema:
        print("Failed to fetch schema")
        return
    
    # Step 2: Extract queries
    print("\nExtracting queries from schema...")
    queries = schema_service.extract_queries(schema)
    print(f"Found {len(queries)} queries")
    
    # Step 3: Run tests
    print("\nRunning tests...")
    test_results = testing_service.batch_test(endpoint, queries, result_service=result_service)
    
    # Step 4: Save results
    print("\nSaving results...")
    result_service.save_test_results(endpoint, test_results)
    
    # Step 5: Ask if user wants to run AI query generation
    while True:
        choice = input("\nDo you want to run AI query generation? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            break
        elif choice in ['n', 'no']:
            print("Skipping AI query generation.")
            return
        else:
            print("Please enter 'y' or 'n'")
    
    print("\n" + "=" * 50)
    print("Starting AI Query Generation...")
    print("=" * 50)
    
    # Generate auth_ok filename based on URL
    filename = endpoint.replace('http://', '').replace('https://', '')
    filename = filename.replace('/', '_').replace(':', '_').replace('.', '_')
    auth_ok_file = f"{output_dir}/{filename}_auth_ok.txt"
    
    if os.path.exists(auth_ok_file):
        run_ai_query_generation(endpoint, auth_ok_file, config)
    else:
        print(f"Auth OK file not found: {auth_ok_file}")


if __name__ == '__main__':
    main()
