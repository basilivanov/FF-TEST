#!/usr/bin/env python3
"""
Тест интеграции новых паттернов в ContextPackager
"""
import os
import json

def test_patterns_integration():
    print("🔍 Тестируем интеграцию паттернов в ContextPackager\n")
    
    # Проверяем существование ключевых файлов
    files_to_check = [
        # Core files
        "/opt/feature-factory/cortex/core/mission.md",
        "/opt/feature-factory/cortex/core/invariants.md", 
        "/opt/feature-factory/cortex/core/subsystems.md",
        "/opt/feature-factory/cortex/core/zero_human_architecture.md",
        
        # Role files
        "/opt/feature-factory/cortex/roles/architect.md",
        "/opt/feature-factory/cortex/roles/dev.md",
        "/opt/feature-factory/cortex/roles/qa.md",
        "/opt/feature-factory/cortex/roles/gate.md",
        "/opt/feature-factory/cortex/roles/scribe.md",
        "/opt/feature-factory/cortex/roles/apply.md",
        
        # Pattern files
        "/opt/feature-factory/cortex/patterns/ai_ml/model_orchestrator.py",
        "/opt/feature-factory/cortex/patterns/ai_ml/learning_engine.py",
        "/opt/feature-factory/cortex/patterns/integrations/marketplace_client.py",
        "/opt/feature-factory/cortex/patterns/testing/playwright_config.ts",
        "/opt/feature-factory/cortex/patterns/testing/e2e_base.ts",
        "/opt/feature-factory/cortex/patterns/subsystems/api_gateway.yaml",
        "/opt/feature-factory/cortex/patterns/validation/gate_examples.py",
        
        # Policy files
        "/opt/feature-factory/cortex/policies/security.md",
        "/opt/feature-factory/cortex/policies/git_workflow.md",
        
        # Contract files
        "/opt/feature-factory/cortex/contracts/architect_examples.yaml",
    ]
    
    print("📁 Проверка существования файлов:")
    missing_files = []
    existing_files = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            file_size = os.path.getsize(file_path)
            print(f"  ✅ {file_path} ({file_size} bytes)")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path} - НЕ НАЙДЕН")
    
    print(f"\n📊 Результат проверки файлов:")
    print(f"  ✅ Существует: {len(existing_files)}")
    print(f"  ❌ Отсутствует: {len(missing_files)}")
    print(f"  📈 Покрытие: {len(existing_files)/(len(existing_files)+len(missing_files))*100:.1f}%")
    
    if missing_files:
        print(f"\n⚠️  Отсутствующие файлы:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    # Анализ эффективности по ролям
    print(f"\n🎯 Анализ эффективности контекста по ролям:")
    
    role_effectiveness = {}
    
    # Architect role
    architect_files = [
        "/opt/feature-factory/cortex/roles/architect.md",
        "/opt/feature-factory/cortex/core/subsystems.md", 
        "/opt/feature-factory/cortex/core/zero_human_architecture.md",
        "/opt/feature-factory/cortex/patterns/subsystems/api_gateway.yaml",
        "/opt/feature-factory/cortex/contracts/architect_examples.yaml"
    ]
    architect_score = sum(1 for f in architect_files if os.path.exists(f)) / len(architect_files) * 100
    role_effectiveness["Architect"] = architect_score
    print(f"  🏗️  Architect: {architect_score:.1f}% эффективности")
    
    # Dev role
    dev_files = [
        "/opt/feature-factory/cortex/roles/dev.md",
        "/opt/feature-factory/cortex/core/invariants.md",
        "/opt/feature-factory/cortex/patterns/ai_ml/model_orchestrator.py", 
        "/opt/feature-factory/cortex/patterns/integrations/marketplace_client.py",
        "/opt/feature-factory/cortex/patterns/testing/api_test_template.py"
    ]
    dev_score = sum(1 for f in dev_files if os.path.exists(f)) / len(dev_files) * 100
    role_effectiveness["Dev"] = dev_score
    print(f"  💻 Dev: {dev_score:.1f}% эффективности")
    
    # QA role
    qa_files = [
        "/opt/feature-factory/cortex/roles/qa.md",
        "/opt/feature-factory/cortex/patterns/testing/playwright_config.ts",
        "/opt/feature-factory/cortex/patterns/testing/e2e_base.ts",
        "/opt/feature-factory/cortex/patterns/testing/coverage_rules.md", 
        "/opt/feature-factory/cortex/patterns/testing/fixture_examples.py"
    ]
    qa_score = sum(1 for f in qa_files if os.path.exists(f)) / len(qa_files) * 100
    role_effectiveness["QA"] = qa_score
    print(f"  🧪 QA: {qa_score:.1f}% эффективности")
    
    # Apply role
    apply_files = [
        "/opt/feature-factory/cortex/roles/apply.md",
        "/opt/feature-factory/cortex/patterns/subsystems/api_gateway.yaml",
        "/opt/feature-factory/cortex/policies/git_workflow.md"
    ]
    apply_score = sum(1 for f in apply_files if os.path.exists(f)) / len(apply_files) * 100
    role_effectiveness["Apply"] = apply_score
    print(f"  🚀 Apply: {apply_score:.1f}% эффективности")
    
    # Gate role
    gate_files = [
        "/opt/feature-factory/cortex/roles/gate.md",
        "/opt/feature-factory/cortex/patterns/validation/gate_examples.py",
        "/opt/feature-factory/cortex/policies/security.md"
    ]
    gate_score = sum(1 for f in gate_files if os.path.exists(f)) / len(gate_files) * 100
    role_effectiveness["Gate"] = gate_score
    print(f"  🛡️  Gate: {gate_score:.1f}% эффективности")
    
    # Scribe role
    scribe_files = [
        "/opt/feature-factory/cortex/roles/scribe.md",
        "/opt/feature-factory/cortex/CHANGELOG.md"
    ]
    scribe_score = sum(1 for f in scribe_files if os.path.exists(f)) / len(scribe_files) * 100
    role_effectiveness["Scribe"] = scribe_score
    print(f"  📝 Scribe: {scribe_score:.1f}% эффективности")
    
    # Общая эффективность
    avg_effectiveness = sum(role_effectiveness.values()) / len(role_effectiveness)
    print(f"\n📈 ОБЩАЯ ЭФФЕКТИВНОСТЬ: {avg_effectiveness:.1f}%")
    
    # Проверка ContextPackager интеграции
    print(f"\n🔧 Проверка интеграции в ContextPackager:")
    
    packager_file = "/opt/feature-factory/app/context/packager.py"
    if os.path.exists(packager_file):
        with open(packager_file, 'r') as f:
            content = f.read()
            
        checks = [
            ('cortex_new/', 'Старые пути cortex_new/'),
            ('/cortex/', 'Новые пути /cortex/'),
            ('model_orchestrator.py', 'AI/ML интеграция'),
            ('marketplace_client.py', 'Marketplace интеграция'), 
            ('playwright_config.ts', 'E2E тестирование'),
            ('learning_engine.py', 'Learning Engine'),
            ('api_gateway.yaml', 'API Gateway паттерны')
        ]
        
        for check, description in checks:
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description}")
    else:
        print(f"  ❌ ContextPackager файл не найден")
    
    print(f"\n🎉 ТЕСТ ЗАВЕРШЕН")
    
    # Итоговые рекомендации
    if avg_effectiveness >= 95:
        print(f"🚀 ОТЛИЧНО! Система готова к production использованию")
    elif avg_effectiveness >= 80:
        print(f"✅ ХОРОШО! Незначительные улучшения нужны")
    else:
        print(f"⚠️  ТРЕБУЕТСЯ ДОРАБОТКА! Критичные паттерны отсутствуют")

if __name__ == "__main__":
    test_patterns_integration()