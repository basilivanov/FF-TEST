# Artifact Manifest

## Описание

Artifact manifest - это спецификация, которая описывает содержимое артефакта, возвращаемого агентами (Dev, QA, Scribe). Manifest должен присутствовать в каждом ответе агента.

## Формат

Manifest должен быть в формате YAML и должен быть первым элементом в ответе агента.

```yaml
# artifact_manifest
- file_path_1
- file_path_2
- file_path_3
```

## Package Contract

Каждый artifact_manifest может содержать package_contract - дополнительную информацию о пакете:

```yaml
# artifact_manifest
- file_path_1
- file_path_2

package_contract:
  package_id: PKG-EXAMPLE-v1
  summary: Краткое описание пакета
  files_layout:
    - file_path_1
    - file_path_2
  db:
    urls:
      test: sqlite:///./test.db
      prod: sqlite:///./prod.db
    tables_touched:
      - table1
      - table2
  index_api:
    symbol: /api/v1/index/symbol
    calls: /api/v1/index/calls
  logging:
    component: api|job|db
    events_must:
      - event1
      - event2
  dod:
    - критерий 1
    - критерий 2
  budget:
    model: flash
    tokens_max: 1000
```

## Валидация

Оркестратор должен валидировать каждый artifact_manifest:
1. Наличие manifest в ответе
2. Корректность формата YAML
3. Наличие package_contract при необходимости
4. Валидация package_contract по schema

## События

При обработке артефактов оркестратор должен логировать следующие события:
- `artifact_rejected` - артефакт отклонен
- `artifact_applied` - артефакт применен успешно
- `index_updated` - индекс обновлен
- `doc_updated` - документ обновлен