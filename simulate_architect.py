#!/usr/bin/env python3
"""
Simulate the Architect AI response for E2E CI testing intent
This shows what the architect should produce for the given intent
"""

import json
from datetime import datetime

def generate_architect_plan():
    """Generate a valid architect plan for E2E CI testing"""
    
    # The input intent
    intent = {
        "action": "test_e2e_ci",
        "params": {
            "description": "Automated E2E test feature for CI/CD pipeline",
            "correlation_id": "28ae6f51-26ae-405d-b5d5-e26b259028f1"
        }
    }
    
    print("🔧 Architect AI Input:")
    print(f"Intent: {json.dumps(intent, indent=2)}")
    print()
    
    # Generate the plan according to the schema
    plan = {
        "dag": {
            "nodes": [
                {
                    "id": "dev_e2e_setup",
                    "role": "Dev",
                    "name": "Setup E2E CI testing infrastructure"
                },
                {
                    "id": "dev_test_automation",
                    "role": "Dev", 
                    "name": "Implement automated E2E test suite"
                },
                {
                    "id": "qa_validation",
                    "role": "QA",
                    "name": "Validate E2E CI pipeline functionality"
                },
                {
                    "id": "scribe_documentation",
                    "role": "Scribe",
                    "name": "Document E2E CI testing procedures"
                },
                {
                    "id": "gate_approval",
                    "role": "Gate",
                    "name": "Final approval for E2E CI deployment"
                }
            ],
            "edges": [
                {
                    "from": "dev_e2e_setup",
                    "to": "dev_test_automation"
                },
                {
                    "from": "dev_test_automation", 
                    "to": "qa_validation"
                },
                {
                    "from": "qa_validation",
                    "to": "scribe_documentation"
                },
                {
                    "from": "scribe_documentation",
                    "to": "gate_approval"
                }
            ]
        },
        "budgets": {
            "Dev": 800,
            "QA": 400,
            "Scribe": 200,
            "Architect": 100
        },
        "dod": [
            "E2E CI pipeline is fully automated",
            "All test scenarios pass successfully", 
            "Performance benchmarks are met",
            "Documentation is complete and accurate",
            "CI/CD integration is validated"
        ]
    }
    
    print("🎯 Architect AI Output:")
    print(json.dumps(plan, indent=2))
    print()
    
    # Validate against schema
    try:
        import jsonschema
        
        # Load the schema
        with open('/opt/feature-factory/configs/schemas/architect.plan.schema.json', 'r') as f:
            schema = json.load(f)
        
        # Validate
        jsonschema.validate(instance=plan, schema=schema)
        print("✅ Plan validates against architect.plan.schema.json")
        
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
    
    print()
    print("📊 Plan Summary:")
    print(f"  • Total tasks: {len(plan['dag']['nodes'])}")
    print(f"  • Roles involved: {set(node['role'] for node in plan['dag']['nodes'])}")
    print(f"  • Total budget: {sum(plan['budgets'].values())} tokens")
    print(f"  • DoD criteria: {len(plan['dod'])}")
    
    return plan

if __name__ == "__main__":
    print("🏗️  Architect AI - E2E CI Plan Generation")
    print("=" * 50)
    plan = generate_architect_plan()
    print("=" * 50)
    print("✅ Architect AI simulation completed successfully!")