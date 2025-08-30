# Визуализация Графа Зависимостей - Техническая Спецификация

**Дата:** 28 августа 2025  
**Статус:** ✅ РЕАЛИЗОВАНО  
**Для:** Mission Critical Admin UI

## 🎯 Что это такое?

**Интерактивная диаграмма зависимостей системы** — визуальное представление того, как модули, API, компоненты и сервисы связаны между собой в Feature Factory.

### Зачем это нужно операционной команде?

1. **🚨 Crisis Response** — при падении модуля сразу видно что затронуто
2. **📊 Performance Monitoring** — узкие места и bottleneck'и видны визуально  
3. **🔧 Impact Analysis** — перед деплоем понятно какие системы затронет изменение
4. **💡 Architecture Understanding** — новые сотрудники быстро понимают структуру

## 🏗️ Архитектура Решения

### Backend (Python/FastAPI)
```
/admin/call-graph API endpoint
├── Подключение к графу вызовов (4,582 рёбер)
├── Фильтрация по типам модулей 
├── Агрегация и группировка
└── JSON API для фронтенда
```

### Frontend (React/D3.js)
```
CallGraphVisualization Component
├── Force-directed graph layout
├── Interactive drag & zoom
├── Color-coded module types
├── Real-time statistics
└── Detail panels
```

## 📱 UI Компоненты

### 1. **System Dependencies Map**
- **Узлы (nodes)** — модули системы (API, LLM, DB, Admin, Graph, Utils)
- **Рёбра (edges)** — вызовы между модулями (толщина = частота)
- **Цветовая схема:**
  - 🔵 API (синий) — внешние интерфейсы
  - 🔴 LLM (красный) — AI обработка  
  - 🟢 Database (зелёный) — данные и модели
  - 🟣 Admin (фиолетовый) — администрирование
  - 🟠 Graph (оранжевый) — граф выполнения
  - ⚫ Utils (серый) — утилиты

### 2. **Mission Critical Indicators**
- **Размер узла** = количество связей (критичность)
- **Толщина линии** = частота вызовов (нагрузка)
- **Hover эффекты** — детали по наведению
- **Click details** — панель с метриками узла

### 3. **Control Panel**
- **Module Filter** — поиск по названию модуля
- **Max Nodes** — ограничение количества (производительность)
- **Refresh** — обновление данных
- **Reset** — сброс фильтров

### 4. **Statistics Dashboard**
- **Total Modules** — общее количество модулей
- **Dependencies** — количество связей
- **Module Types** — распределение по типам
- **Actions** — управляющие кнопки

## 🔧 Интерактивность

### Навигация
- **Zoom** — колесо мыши (0.1x - 4x)
- **Pan** — перетаскивание фона
- **Drag nodes** — перестановка узлов
- **Click node** — детальная информация

### Фильтрация
- По типу модуля (api, llm, db, admin, graph, utils)
- По количеству узлов (10-200)
- По названию модуля

### Анализ
- **Incoming connections** — кто вызывает этот модуль
- **Outgoing connections** — кого вызывает модуль
- **Total connections** — общая критичность
- **File paths** — исходные файлы

## 📊 Use Cases для Mission Critical

### 🚨 **Incident Response**
```
1. Упал модуль API → 
2. Смотрим граф → 
3. Видим что затронуто: LLM router, Database, Admin →
4. Приоритизируем восстановление
```

### 🔧 **Pre-deployment Impact**
```
1. Планируем обновить Database модуль →
2. Смотрим входящие связи →
3. Видим: API, Graph, Tests зависят от DB →
4. Планируем maintenance window
```

### 📈 **Performance Optimization**
```
1. Система тормозит →
2. Находим узлы с наибольшим количеством связей →
3. Анализируем bottleneck'и →
4. Оптимизируем критический путь
```

### 🏗️ **Architecture Planning**
```
1. Добавляем новый компонент →
2. Видим где он должен подключиться →
3. Избегаем создания circular dependencies →
4. Соблюдаем принципы архитектуры
```

## 📁 Файловая Структура

```
/opt/feature-factory/
├── app/admin/
│   ├── routes.py ← обновлен с call-graph endpoint
│   └── call_graph_api.py ← новый API модуль
└── app/ui/src/
    ├── components/
    │   └── CallGraphVisualization.tsx ← основной компонент
    └── pages/
        └── CallGraph.tsx ← страница админки
```

## 🚀 Deployment

### API Endpoint
```bash
GET /api/admin/call-graph?max_nodes=50&module_filter=api
Authorization: Basic b3BzOm9wczEyMw==
```

### UI Route  
```
http://your-domain/admin/call-graph
```

### Dependencies
- **Backend:** SQLAlchemy, FastAPI, structlog
- **Frontend:** React, D3.js, Lucide icons, ShadCN UI

## 🔐 Security

- **Basic Auth** — ops:ops123 (заменить в prod)
- **CORS protection** — только авторизованные домены
- **Rate limiting** — предотвращение DDoS на граф
- **Audit logging** — все запросы логируются

## 📈 Performance

- **Graph caching** — 5 минут TTL
- **Node limiting** — максимум 200 узлов
- **Lazy loading** — детали по требованию
- **WebGL acceleration** — для больших графов (future)

## 🎨 Benefits для вашей команды

### ✅ **Immediate Value**
- Видимость архитектуры системы
- Быстрая диагностика проблем
- Планирование изменений

### ✅ **Long-term Value**  
- Документация архитектуры (self-updating)
- Onboarding новых разработчиков
- Техдолг и рефакторинг планирование

### ✅ **Mission Critical Value**
- **MTTD** (Mean Time To Detection) ↓
- **MTTR** (Mean Time To Recovery) ↓  
- **Change failure rate** ↓
- **Deployment frequency** ↑

---

**Готово к использованию!** 🎉  
Визуализация графа зависимостей полностью интегрирована в вашу админку и готова помочь операционной команде в управлении critical системой.