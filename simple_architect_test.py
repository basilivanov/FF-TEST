#!/usr/bin/env python3
"""
Simple manual architect plan test using stub provider directly
"""
import json

def generate_architect_plan_stub():
    """Generate a sample architect plan for E2E CI testing"""
    
    # This simulates what the stub provider returns
    plan = {
        "dag": {
            "nodes": [
                {
                    "id": "e2e_setup",
                    "role": "Dev", 
                    "name": "Setup E2E test infrastructure"
                },
                {
                    "id": "test_cases",
                    "role": "Dev",
                    "name": "Implement E2E test cases"
                },
                {
                    "id": "ci_integration", 
                    "role": "Dev",
                    "name": "Integrate E2E tests into CI pipeline"
                },
                {
                    "id": "qa_validation",
                    "role": "QA",
                    "name": "Validate E2E test coverage and results"
                }
            ],
            "edges": [
                {"from": "e2e_setup", "to": "test_cases"},
                {"from": "test_cases", "to": "ci_integration"},
                {"from": "ci_integration", "to": "qa_validation"}
            ]
        },
        "budgets": {
            "Dev": 1200,
            "QA": 400
        },
        "dod": [
            "E2E test infrastructure is set up and running",
            "Comprehensive E2E test cases are implemented",
            "Tests are successfully integrated into CI/CD pipeline", 
            "QA has validated test coverage and effectiveness",
            "All tests pass in CI environment"
        ]
    }
    
    return plan

if __name__ == "__main__":
    print("🔧 Generating Architect Plan for E2E CI Testing...")
    
    plan = generate_architect_plan_stub()
    
    # Validate against expected schema structure
    required_fields = ["dag", "budgets", "dod"]
    for field in required_fields:
        if field not in plan:
            print(f"❌ Missing required field: {field}")
            exit(1)
    
    # Validate DAG structure
    dag = plan["dag"]
    if "nodes" not in dag or "edges" not in dag:
        print("❌ Invalid DAG structure")
        exit(1)
    
    # Validate nodes
    for node in dag["nodes"]:
        required_node_fields = ["id", "role", "name"]
        for field in required_node_fields:
            if field not in node:
                print(f"❌ Node missing required field: {field}")
                exit(1)
        
        # Validate role enum
        if node["role"] not in ["Dev", "QA", "Scribe", "Gate", "Apply"]:
            print(f"❌ Invalid role: {node['role']}")
            exit(1)
    
    # Validate edges
    node_ids = {node["id"] for node in dag["nodes"]}
    for edge in dag["edges"]:
        if "from" not in edge or "to" not in edge:
            print("❌ Edge missing required fields")
            exit(1)
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            print(f"❌ Edge references non-existent nodes: {edge}")
            exit(1)
    
    print("✅ Plan structure validation passed!")
    print(f"✅ Generated DAG with {len(dag['nodes'])} tasks and {len(dag['edges'])} dependencies")
    print(f"✅ Budget allocated for {len(plan['budgets'])} roles")
    print(f"✅ {len(plan['dod'])} Definition of Done criteria defined")
    
    print("\n📋 Generated Plan Summary:")
    print("=" * 50)
    
    print("\nTasks:")
    for node in dag["nodes"]:
        print(f"  • [{node['role']}] {node['name']}")
    
    print(f"\nBudgets:")
    for role, tokens in plan["budgets"].items():
        print(f"  • {role}: {tokens} tokens")
    
    print(f"\nDefinition of Done:")
    for i, item in enumerate(plan["dod"], 1):
        print(f"  {i}. {item}")
    
    print("\n✅ Architect Plan generation successful!")
    
    # Optionally output JSON
    print("\n" + "="*50)
    print("JSON Output:")
    print(json.dumps(plan, indent=2))