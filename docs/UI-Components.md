# UI Components Documentation

## Обзор

Этот документ описывает компоненты пользовательского интерфейса Feature Factory Admin UI.

## Компоненты shadcn/ui

### StatusPill

Компонент для отображения статусов в виде цветных бейджей.

**Props:**
- `variant`: 'default' | 'secondary' | 'success' | 'destructive' | 'warning' | 'outline'
- `className`: дополнительные CSS классы
- Все остальные props для HTML span элемента

**Использование:**
```tsx
import { StatusPill } from '@/shadcn/ui/status-pill'

<StatusPill variant="success">Success</StatusPill>
<StatusPill variant="destructive">Error</StatusPill>
```

### DataTable

Компонент для отображения данных в виде таблицы с возможностью фильтрации и пагинации.

**Props:**
- `data`: массив данных для отображения
- `columns`: массив колонок таблицы
- `getKey`: функция для получения уникального ключа для каждой строки
- `className`: дополнительные CSS классы
- `emptyState`: компонент для отображения пустого состояния

**Использование:**
```tsx
import { DataTable } from '@/shadcn/ui/data-table'

const data = [
  { id: 1, name: 'Item 1', value: 'Value 1' },
  { id: 2, name: 'Item 2', value: 'Value 2' },
]

const columns = [
  { key: 'id', title: 'ID' },
  { key: 'name', title: 'Name' },
  { key: 'value', title: 'Value' },
]

<DataTable 
  data={data} 
  columns={columns} 
  getKey={(item) => item.id}
/>
```

### LogViewer

Компонент для отображения логов с возможностью фильтрации, поиска и автопрокрутки.

**Props:**
- `logs`: массив записей логов
- `isStreaming`: флаг потоковой передачи логов
- `onToggleStreaming`: функция для переключения потоковой передачи
- `onClearLogs`: функция для очистки логов
- `className`: дополнительные CSS классы

**Использование:**
```tsx
import { LogViewer } from '@/shadcn/ui/log-viewer'

const logs = [
  {
    ts: '2023-01-01T00:00:00Z',
    level: 'INFO',
    component: 'api',
    agent_role: 'Orchestrator',
    run_id: 'run-001',
    task_id: 'task-001',
    correlation_id: 'corr-001',
    event: 'job_started',
    kv: { job_id: 'job-001' }
  }
]

<LogViewer logs={logs} />
```

### CodeBlock

Компонент для отображения кода с подсветкой синтаксиса и возможностью копирования.

**Props:**
- `code`: код для отображения
- `language`: язык программирования (по умолчанию 'json')
- `className`: дополнительные CSS классы

**Использование:**
```tsx
import { CodeBlock } from '@/shadcn/ui/code-block'

const code = '{"name": "test", "value": 123}'

<CodeBlock code={code} language="json" />
```

### ChatPane

Компонент для отображения чата с возможностью генерации интентов, планов и создания фич.

**Props:**
- `onGenerateIntent`: функция для генерации интента
- `onGeneratePlan`: функция для генерации плана
- `onCreateFeature`: функция для создания фичи
- `onExecutePlan`: функция для выполнения плана
- `className`: дополнительные CSS классы

**Использование:**
```tsx
import { ChatPane } from '@/shadcn/ui/chat-pane'

<ChatPane 
  onGenerateIntent={handleGenerateIntent}
  onGeneratePlan={handleGeneratePlan}
  onCreateFeature={handleCreateFeature}
  onExecutePlan={handleExecutePlan}
/>
```

## Кастомные компоненты

### AppShell

Компонент оболочки приложения с навигационной панелью и основным содержимым.

**Props:**
- `children`: содержимое страницы

**Использование:**
```tsx
import { AppShell } from '@/components/AppShell'

<AppShell>
  <div>Содержимое страницы</div>
</AppShell>
```

## Хуки

### useUIStore

Хук для управления состоянием UI с помощью Zustand.

**Состояние:**
- `theme`: 'light' | 'dark'
- `sidebarCollapsed`: boolean
- `featureFilters`: фильтры для страницы фич
- `taskFilters`: фильтры для страницы задач
- `logFilters`: фильтры для страницы логов

**Методы:**
- `setTheme`: установка темы
- `toggleSidebar`: переключение состояния боковой панели
- `setFeatureFilters`: установка фильтров фич
- `resetFeatureFilters`: сброс фильтров фич
- `setTaskFilters`: установка фильтров задач
- `resetTaskFilters`: сброс фильтров задач
- `setLogFilters`: установка фильтров логов
- `resetLogFilters`: сброс фильтров логов

**Использование:**
```tsx
import { useUIStore } from '@/state/uiStore'

const theme = useUIStore(state => state.theme)
const setTheme = useUIStore(state => state.setTheme)

setTheme('dark')
```

## Утилиты

### API клиент

Клиент для работы с API на основе axios.

**Функции:**
- `apiCall`: базовая функция для API вызовов
- `get`: GET запрос
- `post`: POST запрос
- `put`: PUT запрос
- `del`: DELETE запрос

**Использование:**
```tsx
import { get, post } from '@/lib/api'

const features = await get<Feature[]>('/orchestrator/features')
const newFeature = await post<Feature>('/orchestrator/features', { title: 'New Feature' })
```

### SSE клиент

Клиент для работы с Server-Sent Events.

**Методы:**
- `connect`: подключение к потоку событий
- `disconnect`: отключение от потока событий
- `on`: подписка на события
- `off`: отписка от событий

**Использование:**
```tsx
import { sseClient } from '@/lib/sse'

sseClient.connect('/stream/events')
sseClient.on('job_started', (data) => {
  console.log('Job started:', data)
})
```

### Форматтеры

Функции для форматирования данных.

**Функции:**
- `formatDate`: форматирование даты
- `formatRelativeDate`: форматирование относительной даты
- `formatFeatureStatus`: форматирование статуса фичи
- `formatTaskStatus`: форматирование статуса задачи
- `formatGraphRunStatus`: форматирование статуса запуска графа
- `formatLogLevel`: форматирование уровня лога
- `formatRole`: форматирование роли

**Использование:**
```tsx
import { formatDate, formatFeatureStatus } from '@/lib/format'

const formattedDate = formatDate('2023-01-01T00:00:00Z')
const formattedStatus = formatFeatureStatus('NEW')
```

## DTO

### Feature

```typescript
interface Feature {
  id: number
  title: string
  intent_json: Record<string, unknown> | null
  status: FeatureStatus
  priority: number
  created_at: string
  created_by: string
  env: string
}
```

### Task

```typescript
interface Task {
  id: number
  feature_id: number
  role: Role
  dsl_json: Record<string, unknown>
  status: TaskStatus
  attempts: number
  budget_tokens: number
  scheduled_at: string
  started_at: string | null
  finished_at: string | null
}
```

### GraphRun

```typescript
interface GraphRun {
  run_id: string
  feature_id: number
  graph_name: string
  thread_id: string
  state_json: Record<string, unknown>
  status: GraphRunStatus
  last_checkpoint_at: string
}
```

### LogEntry

```typescript
interface LogEntry {
  ts: string
  level: LogSeverity
  env: string
  component: string
  agent_role: Role
  run_id: string
  task_id: string
  correlation_id: string
  event: string
  kv: Record<string, unknown>
}
```

### TokenUsage

```typescript
interface TokenUsage {
  role: string
  model: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost: number
}
```

### DocRegistryEntry

```typescript
interface DocRegistryEntry {
  doc_name: string
  version: string
  content_hash: string
  updated_at: string
}
```

### MaintainerIntent

```typescript
interface MaintainerIntent {
  nl_text: string
  intent_json: Record<string, unknown>
  issues: string[]
  suggestions: string[]
}
```

### MaintainerPlan

```typescript
interface MaintainerPlan {
  intent_json: Record<string, unknown>
  dag: Array<Record<string, unknown>>
  package_contract: Record<string, unknown>
}
```