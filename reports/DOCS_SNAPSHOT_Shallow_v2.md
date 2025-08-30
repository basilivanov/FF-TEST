# Снапшот документации (Shallow v2)

## Summary

| Root | Files Count | Truncated | Duration (sec) |
|------|-------------|-----------|----------------|
| /opt/feature-factory/docs | 72 | No | 1.00 |
| /opt/feature-factory/cortex | 8 | No | 0.00 |
| /opt/feature-factory/configs | 30 | No | 0.00 |
| /opt/feature-factory/app/ui | 8 | No | 0.00 |
| /opt/feature-factory/cortex/api | 1 | No | 0.00 |
| /opt/feature-factory/agents | 11 | No | 1.00 |

## Table of Contents

- [Backup-and-Recovery-Guide.md](#backup-and-recovery-guide-md)
- [Schemas-Index.md](#schemas-index-md)
- [CLI-Path-Guard.md](#cli-path-guard-md)
- [Architecture.md](#architecture-md)
- [ADR-003-database-url.md](#adr-003-database-url-md)
- [Health-Check-Endpoints.md](#health-check-endpoints-md)
- [Ops-Guide.md](#ops-guide-md)
- [_bundle/artifact_manifest.yaml](#-bundle-artifact-manifest-yaml)
- [_bundle/QA-REPORT.md](#-bundle-qa-report-md)
- [_bundle/FF-Handbook-BUNDLE.md](#-bundle-ff-handbook-bundle-md)
- [_bundle/final_artifact_manifest.yaml](#-bundle-final-artifact-manifest-yaml)
- [_bundle/ops_accept_E12.md](#-bundle-ops-accept-e12-md)
- [_bundle/SOURCE-LIST.json](#-bundle-source-list-json)
- [_bundle/README.md](#-bundle-readme-md)
- [Orch-Prompt-Load-Policy.md](#orch-prompt-load-policy-md)
- [UI-Components.md](#ui-components-md)
- [Alerts-Prompt-Drift.md](#alerts-prompt-drift-md)
- [Permissions-000.md](#permissions-000-md)
- [Commands-UI-000.md](#commands-ui-000-md)
- [UI-Development-Guide.md](#ui-development-guide-md)
- [API-Orchestrator-002-Resume.md](#api-orchestrator-002-resume-md)
- [Router-Enforcement-001.md](#router-enforcement-001-md)
- [LLM-Budgets-001.md](#llm-budgets-001-md)
- [Commands-NL.md](#commands-nl-md)
- [Contracts-Package-Checklist.md](#contracts-package-checklist-md)
- [UI-Testing-Guide.md](#ui-testing-guide-md)
- [UI-Role-Metrics.md](#ui-role-metrics-md)
- [Prompt-Versioning-001.md](#prompt-versioning-001-md)
- [ADR-002-python-version.md](#adr-002-python-version-md)
- [Artifact-Manifest.md](#artifact-manifest-md)
- [Commands-000.md](#commands-000-md)
- [Security-Guide.md](#security-guide-md)
- [Logging-000.md](#logging-000-md)
- [Selectors-DSL-001.md](#selectors-dsl-001-md)
- [API-Testing-Guide.md](#api-testing-guide-md)
- [doc_registry.json](#doc-registry-json)
- [UI-Deployment-Guide.md](#ui-deployment-guide-md)
- [E2E-Testing-Guide.md](#e2e-testing-guide-md)
- [Tokens-Policy-002.md](#tokens-policy-002-md)
- [Schema-000-base-tables.md](#schema-000-base-tables-md)
- [UI-DoD.md](#ui-dod-md)
- [E13-CI-E2E-Implementation-Guide.md](#e13-ci-e2e-implementation-guide-md)
- [Gate-Rules-Roles.md](#gate-rules-roles-md)
- [CI-CD-Guide.md](#ci-cd-guide-md)
- [package_contract.schema.json](#package-contract-schema-json)
- [ChangePolicy-Gate-001.md](#changepolicy-gate-001-md)
- [Nginx-Configuration-Guide.md](#nginx-configuration-guide-md)
- [QA-Checklists/scribe.md](#qa-checklists-scribe-md)
- [QA-Checklists/qa.md](#qa-checklists-qa-md)
- [QA-Checklists/dev.md](#qa-checklists-dev-md)
- [QA-Checklists/architect.md](#qa-checklists-architect-md)
- [QA-Checklists/maintainer.md](#qa-checklists-maintainer-md)
- [UI-Roles-Catalog.md](#ui-roles-catalog-md)
- [CI-RPS.md](#ci-rps-md)
- [UI-Backend-Integration.md](#ui-backend-integration-md)
- [API.md](#api-md)
- [UI-000.md](#ui-000-md)
- [Policy-LLM-000.md](#policy-llm-000-md)
- [Logging-001.md](#logging-001-md)
- [ChangePolicy-000.md](#changepolicy-000-md)
- [ADR-001-stack.md](#adr-001-stack-md)
- [Monitoring-and-Logging-Guide.md](#monitoring-and-logging-guide-md)
- [API-Maintainer-001.md](#api-maintainer-001-md)
- [Context-Scope-Policy.md](#context-scope-policy-md)
- [Ops-DB.md](#ops-db-md)
- [DocSync-Guard-Checklist.md](#docsync-guard-checklist-md)
- [Security-000.md](#security-000-md)
- [Context-Policy-000.md](#context-policy-000-md)
- [API-Orchestrator-001.md](#api-orchestrator-001-md)
- [DoD-000.md](#dod-000-md)
- [QA-Policy-001.md](#qa-policy-001-md)
- [LangGraph-Nodes-Contracts.md](#langgraph-nodes-contracts-md)
- [api/openapi.spec.json](#api-openapi-spec-json)
- [db_rules.md](#db-rules-md)
- [security/credentials.md](#security-credentials-md)
- [playbook/main.md](#playbook-main-md)
- [doctrine/common_rules.md](#doctrine-common-rules-md)
- [db/rules.md](#db-rules-md)
- [ops_tools.md](#ops-tools-md)
- [logging_rules.md](#logging-rules-md)
- [llm_cli_config.yaml](#llm-cli-config-yaml)
- [feature-factory-test.service](#feature-factory-test-service)
- [feature-factory-prod.service](#feature-factory-prod-service)
- [prompts.yaml](#prompts-yaml)
- [prompts.lock.json](#prompts-lock-json)
- [nginx/etl-tst.chococraft.ru.backup](#nginx-etl-tst-chococraft-ru-backup)
- [nginx/etl-tst.chococraft.ru.conf](#nginx-etl-tst-chococraft-ru-conf)
- [nginx/etl-tst.chococraft.ru](#nginx-etl-tst-chococraft-ru)
- [nginx/.htpasswd](#nginx--htpasswd)
- [nginx/etl.chococraft.ru](#nginx-etl-chococraft-ru)
- [litellm.service](#litellm-service)
- [llm_routing_v2.yaml](#llm-routing-v2-yaml)
- [resource_manifest.yaml](#resource-manifest-yaml)
- [bootstrap.yaml](#bootstrap-yaml)
- [docs_snapshot_policy.yaml](#docs-snapshot-policy-yaml)
- [llm_cli.yaml](#llm-cli-yaml)
- [schemas/qa.report.schema.json](#schemas-qa-report-schema-json)
- [schemas/maintainer.intent.schema.json](#schemas-maintainer-intent-schema-json)
- [schemas/scribe.changelog.schema.json](#schemas-scribe-changelog-schema-json)
- [schemas/artifact_manifest.schema.json](#schemas-artifact-manifest-schema-json)
- [schemas/architect.plan.schema.json](#schemas-architect-plan-schema-json)
- [routing.stub.yaml](#routing-stub-yaml)
- [feature-factory-test.env](#feature-factory-test-env)
- [ops/sudo_wrappers.yaml](#ops-sudo-wrappers-yaml)
- [views.yaml](#views-yaml)
- [litellm.yaml](#litellm-yaml)
- [watchdog_policy.yaml](#watchdog-policy-yaml)
- [llm_routing.yaml](#llm-routing-yaml)
- [llm_budgets.yaml](#llm-budgets-yaml)
- [feature-factory-prod.env](#feature-factory-prod-env)
- [node_modules.backup.1756360811/.package-lock.json](#node-modules-backup-1756360811--package-lock-json)
- [node_modules.backup.1756282805/.package-lock.json](#node-modules-backup-1756282805--package-lock-json)
- [nl_intents.yaml](#nl-intents-yaml)
- [package-lock.json](#package-lock-json)
- [tsconfig.node.json](#tsconfig-node-json)
- [package.json](#package-json)
- [node_modules.backup.1756282346/.package-lock.json](#node-modules-backup-1756282346--package-lock-json)
- [tsconfig.json](#tsconfig-json)
- [openapi.spec.json](#openapi-spec-json)
- [prompts/scribe.md](#prompts-scribe-md)
- [prompts/qa.md](#prompts-qa-md)
- [prompts/maintainer_chat.md](#prompts-maintainer-chat-md)
- [prompts/dev.md](#prompts-dev-md)
- [prompts/architect.md](#prompts-architect-md)
- [prompts/maintainer.md](#prompts-maintainer-md)
- [charters/scribe.md](#charters-scribe-md)
- [charters/qa.md](#charters-qa-md)
- [charters/dev.md](#charters-dev-md)
- [charters/architect.md](#charters-architect-md)
- [charters/maintainer.md](#charters-maintainer-md)

## Master Table

| # | Path | Type | Size | Lines | SHA256 Head | MTime |
|---|------|------|------|-------|-------------|-------|
| 1 | Backup-and-Recovery-Guide.md | Markdown | 12893 | 388 | 7b41ed08b9304bb43a5c36f9e584dc5f3e05cca6217c3b57f1ea4b66cdf62ab8 | 1755819543 |
| 2 | Schemas-Index.md | Markdown | 718 | 15 | 93894cdeea2d05ade1cbe1f1c6b24fe8a53309eb3f00dbdd3b59d6c7375a7770 | 1756125029 |
| 3 | CLI-Path-Guard.md | Markdown | 2602 | 94 | e4c7b9f342a15e00aa9445bf5b2b5efdca76966c3789089c3871a095ab2c0b8a | 1755861627 |
| 4 | Architecture.md | Markdown | 10399 | 122 | 816d6ab2d983b3bef6fcc4426c1e40ca01f374e21caba4d2c23b72b144176549 | 1756494978 |
| 5 | ADR-003-database-url.md | Markdown | 2690 | 21 | da8ba5288a61ee2e7af64b92572049d6eeeff645bc59ebeea2c299b1b4c084ea | 1755866834 |
| 6 | Health-Check-Endpoints.md | Markdown | 4313 | 146 | a3ef19928b3c5465065a4bb5e14172ed17226ffd9f194a22fd113e5a61307727 | 1755861606 |
| 7 | Ops-Guide.md | Markdown | 3206 | 27 | abbad2c07d637206002053a07584fc92ebb43ce2df86583f342d0439de4b92b9 | 1756243524 |
| 8 | _bundle/artifact_manifest.yaml | YAML | 125 | 5 | 51229ecb5bfb5be8703f5e191e030670ef0d576fedfb5e3f7a58e1c6f96bee25 | 1755787233 |
| 9 | _bundle/QA-REPORT.md | Markdown | 2335 | 38 | d5a17df277125cd3dc6677223d647a53e7a8a73f90948ca4725c7b41addb81fb | 1755787335 |
| 10 | _bundle/FF-Handbook-BUNDLE.md | Markdown | 95032 | 2412 | 54d1eee0e25b19f12c0475222ef1321ca8a8d7788fddefd7958f7f3aad687343 | 1755809869 |
| 11 | _bundle/final_artifact_manifest.yaml | YAML | 125 | 5 | 51229ecb5bfb5be8703f5e191e030670ef0d576fedfb5e3f7a58e1c6f96bee25 | 1755787339 |
| 12 | _bundle/ops_accept_E12.md | Markdown | 3566 | 78 | 9faf049c2b00e006377cf36059396b8d3f65a13fe8ad39ee2a2395e5490de917 | 1755876892 |
| 13 | _bundle/SOURCE-LIST.json | JSON | 4526 | 46 | da89521c97a4655923cf1e4667b8bcbf80e961b0c47f2ec43659025d81bc8340 | 1755812453 |
| 14 | _bundle/README.md | Markdown | 1343 | 29 | 97f5ff23dedd9152c92555d74c470cc316fd601cde56eda9a100a10fe59af039 | 1755787222 |
| 15 | Orch-Prompt-Load-Policy.md | Markdown | 3219 | 69 | 65c31dfd4fc1459c95402ef703ecbd1ee49f9a0bd92bfcce499bfe5d62b58a37 | 1756125630 |
| 16 | UI-Components.md | Markdown | 9250 | 352 | fe2c928b28666616f670fd788b5134b26070868e1e5eeaec0090c74e25716d31 | 1755818278 |
| 17 | Alerts-Prompt-Drift.md | Markdown | 13468 | 353 | aec8dfe206dcb34ac167ee87e6ae86468259b2583657678412dd7a0994fdd410 | 1756127034 |
| 18 | Permissions-000.md | Markdown | 932 | 10 | c2f68f5a47d71e177191e5905d9dc359eaa9dab5434be07f03dcf72ed828ea0d | 1756125020 |
| 19 | Commands-UI-000.md | Markdown | 5522 | 147 | ed5576991d853b50f6d22e76d262a8ffe27ca1d37038385ed5ba6a3d743ef64b | 1755818120 |
| 20 | UI-Development-Guide.md | Markdown | 15387 | 539 | a1b5ca64da0ca1938b982aa9d45a54d046c62e4fb76009d29a0d3bbceda71d5c | 1755818392 |
| 21 | API-Orchestrator-002-Resume.md | Markdown | 6102 | 108 | 8a9b30e766073ec4ddcec406592dc05564447f6e5d87c8bf450e66d9518f2c5c | 1755866961 |
| 22 | Router-Enforcement-001.md | Markdown | 7021 | 186 | 27d1c6c4ac8d8510500da5b21e5a0465df3b34a1b5be97fcfd811c48ba2a625d | 1756126559 |
| 23 | LLM-Budgets-001.md | Markdown | 1012 | 20 | 032ec6acd75200dd2414d94a70f703efb2984e601945cee2667b4e2b11cc9175 | 1756239688 |
| 24 | Commands-NL.md | Markdown | 1912 | 28 | 38b0bb9f74efc3eb4b1a307a29656873f11ac5d4763e4887be0f4f1f1dad007e | 1755789766 |
| 25 | Contracts-Package-Checklist.md | Markdown | 5562 | 166 | a9a734243d307f402b22e6328ef1fa6d8de8b318fa48691e9639ff62c92c6f52 | 1756125685 |
| 26 | UI-Testing-Guide.md | Markdown | 4115 | 109 | 147945e0b3166e5464918a83bf544cc4993c0cf8bb9fd0c4a37ede548e1a3a63 | 1755821332 |
| 27 | UI-Role-Metrics.md | Markdown | 9526 | 228 | 424cbc4260e3a8c0257748d941baf760d5dd34e46ff4a9546cbe2e6d944c740d | 1756126712 |
| 28 | Prompt-Versioning-001.md | Markdown | 8299 | 186 | 0d39c11549ff57e4032fef2c1030bc946a1ff0df7dae92779f3088a38f9ad157 | 1756126529 |
| 29 | ADR-002-python-version.md | Markdown | 1692 | 32 | 7d80693c5114645e7b765e97caf5db861f2ba3d8beb010d28d8c428ad4553399 | 1755793345 |
| 30 | Artifact-Manifest.md | Markdown | 2061 | 69 | eaa6bb1221cbf82c3c6c1d2a8d2adacb8f136182672ca1846c4bbb3fbf461a74 | 1755790934 |
| 31 | Commands-000.md | Markdown | 813 | 12 | 8a922679cf521a6a1b5d195721359311348df303b9a5b9a0ed1a6a7417524c7f | 1755779810 |
| 32 | Security-Guide.md | Markdown | 10724 | 286 | b9705309bec4a5df01878c59c0da599c404177b358cb926521cba22e93589040 | 1756494984 |
| 33 | Logging-000.md | Markdown | 99 | 2 | 6b5b2f2dfb90fd0793a35da4101de3bd81694d1877b0abd3045bdf4d70f6c2be | 1755779810 |
| 34 | Selectors-DSL-001.md | Markdown | 758 | 24 | 6d54881d7ca9aea284578a6df7dc837a1b894d456658af3f1da17e8cbd6fa417 | 1756125013 |
| 35 | API-Testing-Guide.md | Markdown | 8799 | 249 | 8bfb6ce873da7a7af87b86cd3fda26b0c20809b0b7507a75b5f5e6c1c440c475 | 1755819143 |
| 36 | doc_registry.json | JSON | 7831 | 285 | 3ccfc005fd291c1170bef70d936a859ced709432a9e61aecef25fd04a1d9316c | 1756127105 |
| 37 | UI-Deployment-Guide.md | Markdown | 5906 | 191 | 67c01be86381adf92186bb02e77616d80eac9d3e42f6ca3a817ad8c765c5b5cd | 1755818246 |
| 38 | E2E-Testing-Guide.md | Markdown | 16667 | 546 | 5b48216a958a1ba51704b1cb4489cc858930539dace2c4f11fce883fcd87415d | 1755821614 |
| 39 | Tokens-Policy-002.md | Markdown | 3261 | 82 | 8effcf0dec49da1d575e852140112a2e12791e35096b36d7f44ce3db98ce1dd4 | 1756125710 |
| 40 | Schema-000-base-tables.md | Markdown | 4801 | 125 | 3cdf3261d93d76d3c41b92c47963ef50154a3d911c88813a5f064e10287b456d | 1755866979 |
| 41 | UI-DoD.md | Markdown | 14143 | 237 | 996e3a265c45cf87d2f6d6c85ddccc76081f4bff2d0f8c38b051f1d5a686e8ad | 1755820622 |
| 42 | E13-CI-E2E-Implementation-Guide.md | Markdown | 9353 | 260 | 08828d65dbb414b1b60f9691a048de6ca5d76dc9330f65bc491829022c507e3f | 1755878656 |
| 43 | Gate-Rules-Roles.md | Markdown | 3562 | 116 | 2031c3998fb9e208d502080b529bddefaf2915baed3034e02fb88302f1476184 | 1756125657 |
| 44 | CI-CD-Guide.md | Markdown | 19842 | 605 | cfd91da57c8a9250d2d7594e39e71a1067e2a1a8bbd42b4c2c4d9f7863cf0d85 | 1755819709 |
| 45 | package_contract.schema.json | JSON | 1851 | 88 | 2a7ec59341b4a9025f5b9f70b77b24b00d312b78e78b1ea22456fd8cd8ad41b6 | 1755790923 |
| 46 | ChangePolicy-Gate-001.md | Markdown | 920 | 15 | d5789590ac3fdb944d31aa7ae9942da5b98c98b875083cf8d63e3e039b3d8446 | 1756125034 |
| 47 | Nginx-Configuration-Guide.md | Markdown | 7213 | 208 | f2cecc4d2ba6844e719c74adffbe3208cca67c2994bc925758006ef0bd65e416 | 1755823681 |
| 48 | QA-Checklists/scribe.md | Markdown | 1505 | 18 | 3584843994b31b74e0fd714504a5c3cc8768cc066e0c05b757458c12e294a50e | 1756125464 |
| 49 | QA-Checklists/qa.md | Markdown | 1466 | 18 | c29d5635a4709414d8348da9b7b6dd29a120915b15b57edfc11ac6361280c7e9 | 1756125452 |
| 50 | QA-Checklists/dev.md | Markdown | 1323 | 17 | f93384800f3fe5fcc55086661fe1a8f3cd9248937f9cae74e43e8357ba9da7c1 | 1756125050 |
| 51 | QA-Checklists/architect.md | Markdown | 1443 | 18 | bb8d1a905655264ac215ad7356cd0c8f3566973cd014529aa1458d179da1be33 | 1756125444 |
| 52 | QA-Checklists/maintainer.md | Markdown | 1376 | 18 | 7b35552ec8108fea71854d9a00a4d0302605c41063c064f41829c0c616c7e1fa | 1756125471 |
| 53 | UI-Roles-Catalog.md | Markdown | 4371 | 111 | a07b4ec92fff972d94017ff01db79ff9464e2e0235a6ca3f05799f5ac8e9e153 | 1756125747 |
| 54 | CI-RPS.md | Markdown | 16570 | 452 | bdb3c485c690282dcc407ea530f474bb9c5eca7f56d383aca0325544ff4c2adb | 1756126974 |
| 55 | UI-Backend-Integration.md | Markdown | 9181 | 383 | 32db0f727f876e208a6e3a45799435de511a017246b3850050c2de6acc6e1918 | 1755818325 |
| 56 | API.md | Markdown | 15082 | 0 | 69169e51d5d3f487a2536b4868ab22bf058f44b46d5e6c27510f663246d9c019 | 1755818595 |
| 57 | UI-000.md | Markdown | 699 | 21 | c73e8e4ef28b1a8c8b7bba25031c624be6d6ec0f49fa77d95b67a91cf7f29881 | 1756125509 |
| 58 | Policy-LLM-000.md | Markdown | 2853 | 49 | ddde33801a9bc3fa21a97e3398919ef5e695acfec764885840c9e1b0f08de6c1 | 1756239676 |
| 59 | Logging-001.md | Markdown | 2271 | 39 | 0bf0719167c2c115016392dec5f212c35c2167f753786401b07715f4c944a32e | 1755788984 |
| 60 | ChangePolicy-000.md | Markdown | 3914 | 83 | ee95dce34fb44d2810c1ace4f895d7497c6702d693d7c167e5ccbcd5926f229b | 1755867012 |
| 61 | ADR-001-stack.md | Markdown | 941 | 9 | 01581260c53d8794c0ed0b0508769a9aa79e08fdab6ef55c46282878d80de476 | 1755779810 |
| 62 | Monitoring-and-Logging-Guide.md | Markdown | 17341 | 600 | 0da3784ae5ada7ae968aa61921ca3960dff7fdb84358f6061b85984facdc41da | 1755819309 |
| 63 | API-Maintainer-001.md | Markdown | 1425 | 47 | 0c191cad8230df13d1ec6ed6d9482891cdefc45b31685a084be4d9e054df0846 | 1756125502 |
| 64 | Context-Scope-Policy.md | Markdown | 8327 | 164 | 544c161b7e3b8f8d2e9131c47bb0af2748632a0f7c96c67bd4a99c50a680d8c9 | 1756126784 |
| 65 | Ops-DB.md | Markdown | 2661 | 47 | d4ae2e25525a7f2470b48102ad7fbfc756e61538e3c6da5f5c583623fe43c9d2 | 1755866858 |
| 66 | DocSync-Guard-Checklist.md | Markdown | 5565 | 71 | ddd00024a3754f7bfe580e535d6b0f1778b5610d9b9d04aa1f8e93e23ed2dc82 | 1755867033 |
| 67 | Security-000.md | Markdown | 538 | 6 | 1bf62d6b16b21511d43d1c1d315baef21a6ab763c86c101a927a565376a1e941 | 1755779810 |
| 68 | Context-Policy-000.md | Markdown | 1278 | 20 | 544c161b7e3b8f8d2e9131c47bb0af2748632a0f7c96c67bd4a99c50a680d8c9 | 1756125001 |
| 69 | API-Orchestrator-001.md | Markdown | 4951 | 217 | 5db05c91b0044a1b658d5798c1dfba09ff6abeeb02591df80cf696d12f5cc08c | 1755867690 |
| 70 | DoD-000.md | Markdown | 451 | 5 | 8a8d6c57edc330a3e4cfb2af36f7d0dcd995afa4b884ffb135e01ab7a158b0ca | 1755779810 |
| 71 | QA-Policy-001.md | Markdown | 2591 | 49 | a93013deb261fe7193f58a9f1955d0a41ee341ff0aeffde383e6992e5243f08a | 1755862692 |
| 72 | LangGraph-Nodes-Contracts.md | Markdown | 1391 | 38 | d692162c07250a8453926f008350f612526e15a3d565f061661abc16e5fc9130 | 1756125489 |
| 73 | api/openapi.spec.json | JSON | 65866 | 0 | 032273c138626fe515ef7e685b71ac83d555241acefcd270bada084c986ea1e0 | 1756557910 |
| 74 | db_rules.md | Markdown | 200 | 4 | 0224d2fa7274f8dbfabcd073e75dd92afbbd0e1c3b6aace6bb21fdfbd4ccc143 | 1756369508 |
| 75 | security/credentials.md | Markdown | 2991 | 76 | b098efac4f3fd664d20b74a26440e91d4986e2aa4522e890f2d6e084973f44ee | 1756374784 |
| 76 | playbook/main.md | Markdown | 4811 | 24 | 24a7e57d60defbe50330f2cf396bb526559c40ded973ade2403f625773668673 | 1756502254 |
| 77 | doctrine/common_rules.md | Markdown | 6186 | 138 | 929fc5549a09ad5f5df86128877b2d10ae823104c660fe0d76502c1fa6757918 | 1756374831 |
| 78 | db/rules.md | Markdown | 486 | 3 | 3062e764fa98bdf42afcc03bb1b5dd953c8f2dee898d4c4bb4d972a64cd65dd7 | 1756371444 |
| 79 | ops_tools.md | Markdown | 710 | 14 | 44e0dc0c7d6c908eb6b12a458f79d6877a1e04dfecf76d1c8b4482c52b8567be | 1756369519 |
| 80 | logging_rules.md | Markdown | 592 | 8 | b08836693249fa12fea47f4dbc1968d9f80c3263f139f33f4dde910bb1407b82 | 1756369532 |
| 81 | llm_cli_config.yaml | YAML | 4548 | 114 | c8dd35638716db5c1f93bd589c104996c8bfd395a00ddb21d368f3ba6706c100 | 1756462228 |
| 82 | feature-factory-test.service | Other | 477 | 18 | e7c47d3ce0a52d4b859fd85bf7d2e34cf882f570321bdeede63f90ed7c33e81d | 1755793511 |
| 83 | feature-factory-prod.service | Other | 484 | 18 | e7c47d3ce0a52d4b859fd85bf7d2e34cf882f570321bdeede63f90ed7c33e81d | 1755793507 |
| 84 | prompts.yaml | YAML | 1577 | 65 | e9a485d2e1f168ff236528436033ef5d171140b6c7c05e50ea6af7ba42e343ae | 1756324849 |
| 85 | prompts.lock.json | JSON | 979 | 28 | 3014fa483fa4980de9cf9d045b73225389160eb5b12f88f1c2451235073de997 | 1756126537 |
| 86 | nginx/etl-tst.chococraft.ru.backup | Other | 3923 | 99 | 802772a546c45e910280a67f30f7f95f8809afcb30c5aeb99e2a1b3e2beff181 | 1755875161 |
| 87 | nginx/etl-tst.chococraft.ru.conf | Other | 2949 | 76 | 802772a546c45e910280a67f30f7f95f8809afcb30c5aeb99e2a1b3e2beff181 | 1755890380 |
| 88 | nginx/etl-tst.chococraft.ru | Other | 4290 | 112 | 802772a546c45e910280a67f30f7f95f8809afcb30c5aeb99e2a1b3e2beff181 | 1756537704 |
| 89 | nginx/.htpasswd | Other | 42 | 1 | 8617bb4479d7f0de8629d3ef964edf4174aae73fa52c788a5082a8904f6da456 | 1755876256 |
| 90 | nginx/etl.chococraft.ru | Other | 1210 | 32 | 802772a546c45e910280a67f30f7f95f8809afcb30c5aeb99e2a1b3e2beff181 | 1755793503 |
| 91 | litellm.service | Other | 273 | 14 | cb501458ebac636d30c71fe4bf305b9a141c85cb9c865ea89c80338a404d0916 | 1755796381 |
| 92 | llm_routing_v2.yaml | YAML | 893 | 50 | 49e2cd4178846adfc71149b213de8b4ef2e34f2a1ce5edb0e6426a54e4c7adb8 | 1756125691 |
| 93 | resource_manifest.yaml | YAML | 437 | 6 | bae6bad2e2a1b09cd9ee635e45ffcd1d542556f99a78fdaac81bd8b200eba391 | 1756358606 |
| 94 | bootstrap.yaml | YAML | 66 | 2 | fd68dd4f3c50e30f75817a9bc5c74695462c26a6fbcb70480ab07e76690d2ffe | 1756502245 |
| 95 | docs_snapshot_policy.yaml | YAML | 339 | 6 | d2e9a9998e464790b8451dc59e456454cbd1c0776a8bfeaff21e6c18c348a82a | 1756563200 |
| 96 | llm_cli.yaml | YAML | 2554 | 74 | 4aa7c8f930ebddf56422033529c99d30cfd665043186f17acfa988acf2dfb3f8 | 1756446099 |
| 97 | schemas/qa.report.schema.json | JSON | 754 | 28 | 84ecbdb6b816278e0bbafe32cd7c57f90583d4482ec5f7c6190c0eff0769773c | 1756140323 |
| 98 | schemas/maintainer.intent.schema.json | JSON | 1206 | 45 | 84ecbdb6b816278e0bbafe32cd7c57f90583d4482ec5f7c6190c0eff0769773c | 1756140316 |
| 99 | schemas/scribe.changelog.schema.json | JSON | 688 | 24 | 84ecbdb6b816278e0bbafe32cd7c57f90583d4482ec5f7c6190c0eff0769773c | 1756140326 |
| 100 | schemas/artifact_manifest.schema.json | JSON | 704 | 28 | 2a7ec59341b4a9025f5b9f70b77b24b00d312b78e78b1ea22456fd8cd8ad41b6 | 1756243780 |
| 101 | schemas/architect.plan.schema.json | JSON | 1515 | 56 | 84ecbdb6b816278e0bbafe32cd7c57f90583d4482ec5f7c6190c0eff0769773c | 1756140319 |
| 102 | routing.stub.yaml | YAML | 988 | 10 | be3d8da5b7ebe2e788bb03df9d967a0ed135090eda8058aee5d4746cc218f88a | 1756248932 |
| 103 | feature-factory-test.env | Other | 195 | 6 | fe8fa1f360b32f5adcb5d4e2509c1b8b9f6c7517cea39bbe284c0c495bcdaf2d | 1756315743 |
| 104 | ops/sudo_wrappers.yaml | YAML | 618 | 11 | 975ba820cf3f7b8088c74184d1cd2ba8341303cd841ff32ca46e1ad0b0f32339 | 1756243493 |
| 105 | views.yaml | YAML | 489 | 21 | f92f8a0fb91f7f4ccae6962567a7d0aa3780ef88fe2c727d57dfa04a97aeeb9c | 1755779810 |
| 106 | litellm.yaml | YAML | 1124 | 44 | 5bbe3d072436a6c0c68de3c591124341e3e4f1556ad4c2f78bde8dcf7bdbafbc | 1755796297 |
| 107 | watchdog_policy.yaml | YAML | 329 | 13 | cc6152586e347e814d634fb186d0230b0fd389e053d818ddee33657fc5189a21 | 1756325454 |
| 108 | llm_routing.yaml | YAML | 3009 | 88 | c665c575d9767ef64ffd3ef9b0dbca12c69289b2c250e6d6cc02c1edd6b53526 | 1756446261 |
| 109 | llm_budgets.yaml | YAML | 456 | 10 | 5cbce26f9a24da99aa8698cbf6e70089079325f8b429b588240038293d389105 | 1756309221 |
| 110 | feature-factory-prod.env | Other | 163 | 5 | f9b038935f81ccdd7a0060215bf7a4f4346baaa7233269488cb7e51a5d66ea13 | 1755793565 |
| 111 | node_modules.backup.1756360811/.package-lock.json | JSON | 338638 | 9450 | c2ad2e65dba0b27cd12c062eb42c0fcaef4dc1b9e3f40c5156f88f22906c5623 | 1756359088 |
| 112 | node_modules.backup.1756282805/.package-lock.json | JSON | 338638 | 9450 | c2ad2e65dba0b27cd12c062eb42c0fcaef4dc1b9e3f40c5156f88f22906c5623 | 1756282355 |
| 113 | nl_intents.yaml | YAML | 1259 | 41 | f51018da2e7c64f9d2001d0776839668e0382e17688e6f8a12968fb0f9b5c572 | 1755779810 |
| 114 | package-lock.json | JSON | 371001 | 10410 | c2ad2e65dba0b27cd12c062eb42c0fcaef4dc1b9e3f40c5156f88f22906c5623 | 1756374198 |
| 115 | tsconfig.node.json | JSON | 212 | 9 | c4c24277b6d9137e6a92877d741979b09b510cbb31cad9a6dff7e46f9d3905cf | 1755810229 |
| 116 | package.json | JSON | 2115 | 64 | c2ad2e65dba0b27cd12c062eb42c0fcaef4dc1b9e3f40c5156f88f22906c5623 | 1756374134 |
| 117 | node_modules.backup.1756282346/.package-lock.json | JSON | 338638 | 9450 | c2ad2e65dba0b27cd12c062eb42c0fcaef4dc1b9e3f40c5156f88f22906c5623 | 1756280818 |
| 118 | tsconfig.json | JSON | 701 | 32 | b5ffbf6a59a666e6f3d67070a6b8e59ed2c7810d30f2b815b02db9b0988d25bc | 1755881468 |
| 119 | openapi.spec.json | JSON | 65866 | 0 | 032273c138626fe515ef7e685b71ac83d555241acefcd270bada084c986ea1e0 | 1756557910 |
| 120 | prompts/scribe.md | Markdown | 673 | 22 | d6d3c823e0a1ad9ce9d6e67443b2a02899acc4e47abc4f634902a45658999f47 | 1756124985 |
| 121 | prompts/qa.md | Markdown | 934 | 25 | c0d5796dea5ed0eaf60b5c73c73e0bbca1d20daed80eb3c02f083d1c78fe1ec7 | 1756124976 |
| 122 | prompts/maintainer_chat.md | Markdown | 3180 | 56 | ae3cd2b32483c0e0f06446244c5e38810924b5cff0f2e82c4d84d007440a6065 | 1756289397 |
| 123 | prompts/dev.md | Markdown | 1020 | 25 | 45fab46a2821b60f11b2aacdc02c3d964ddc61439d99f7653131246e9fd4ab79 | 1756124970 |
| 124 | prompts/architect.md | Markdown | 1459 | 29 | 87d64fd5d5f2d7c4903c0d91a4142d9e3bff9b59408cb5c0bd7fe4e632087dab | 1756124964 |
| 125 | prompts/maintainer.md | Markdown | 760 | 23 | ae3cd2b32483c0e0f06446244c5e38810924b5cff0f2e82c4d84d007440a6065 | 1756124993 |
| 126 | charters/scribe.md | Markdown | 1197 | 35 | 41b94e13e28dff1f992431cd82940c5b12d635748efaae9ee20cc0b70f523e5b | 1756124942 |
| 127 | charters/qa.md | Markdown | 1474 | 36 | 07eb0fa4c5920951974e54aba91fe51c1c8443e658de519ae007dc999a2353cb | 1756124935 |
| 128 | charters/dev.md | Markdown | 1764 | 39 | 089aafba3d84ee6a8693f8ee409996bec25b9fe4018fc885602df2a33d1a0ea6 | 1756124925 |
| 129 | charters/architect.md | Markdown | 2307 | 44 | 30596f3e8d7d7d57e2c449894365117d2cfd80a32b662ada86fd8fd9415b5ffb | 1756124916 |
| 130 | charters/maintainer.md | Markdown | 1443 | 35 | b6654451c677d65145f9064aeae4074e7b74b508d4532a47c0ba61cd35d50c30 | 1756124953 |

## Content Previews

