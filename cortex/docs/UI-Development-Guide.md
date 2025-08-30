# UI Development Guide

## Обзор

Этот документ описывает процесс разработки пользовательского интерфейса Feature Factory Admin UI.

## Стек технологий

- **Фреймворк**: React 18
- **Язык**: TypeScript
- **Сборщик**: Vite
- **Стилизация**: Tailwind CSS
- **Компоненты**: shadcn/ui (на базе Radix UI)
- **Управление состоянием**: Zustand
- **HTTP клиент**: Axios
- **Роутинг**: React Router
- **Форматирование кода**: Prettier
- **Линтинг**: ESLint
- **Тестирование**: Jest, React Testing Library

## Структура проекта

```
app/ui/
  src/
    assets/          # Статические файлы
    components/      # Кастомные компоненты
    lib/             # Библиотечные функции
    pages/           # Страницы приложения
    shadcn/          # Компоненты shadcn/ui
    state/           # Управление состоянием
    App.tsx          # Корневой компонент
    main.tsx         # Точка входа
    routes.tsx       # Конфигурация роутинга
    app.css          # Глобальные стили
  public/            # Публичные файлы
  index.html         # HTML шаблон
  package.json       # Зависимости и скрипты
  tsconfig.json      # Конфигурация TypeScript
  vite.config.ts     # Конфигурация Vite
```

## Установка и запуск

### Предварительные требования

- Node.js >= 16.0.0
- npm >= 8.0.0

### Установка зависимостей

```bash
cd /opt/feature-factory/app/ui
npm install
```

### Запуск в режиме разработки

```bash
cd /opt/feature-factory/app/ui
npm run dev
```

Приложение будет доступно по адресу http://localhost:5173

### Сборка для продакшена

```bash
cd /opt/feature-factory/app/ui
npm run build
```

### Предварительный просмотр продакшен сборки

```bash
cd /opt/feature-factory/app/ui
npm run preview
```

### Линтинг

```bash
cd /opt/feature-factory/app/ui
npm run lint
```

### Исправление ошибок линтинга

```bash
cd /opt/feature-factory/app/ui
npm run lint:fix
```

## Разработка компонентов

### Создание нового компонента

1. Создайте файл компонента в `src/components/`
2. Используйте TypeScript для типизации
3. Экспортируйте компонент по умолчанию
4. Добавьте тесты в `src/components/__tests__/`

Пример компонента:

```tsx
// src/components/MyComponent.tsx
import React from 'react'

interface MyComponentProps {
  title: string
  onClick?: () => void
}

const MyComponent: React.FC<MyComponentProps> = ({ title, onClick }) => {
  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h2 className="text-xl font-bold">{title}</h2>
      <button 
        onClick={onClick}
        className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
      >
        Click me
      </button>
    </div>
  )
}

export default MyComponent
```

### Использование компонентов shadcn/ui

Компоненты shadcn/ui находятся в `src/shadcn/ui/`. Импортируйте их напрямую:

```tsx
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
```

### Создание нового компонента shadcn/ui

Для создания нового компонента shadcn/ui используйте CLI:

```bash
npx shadcn-ui@latest add button
```

## Разработка страниц

### Создание новой страницы

1. Создайте файл страницы в `src/pages/`
2. Используйте TypeScript для типизации
3. Экспортируйте компонент страницы по умолчанию
4. Добавьте маршрут в `src/routes.tsx`
5. Добавьте ссылку в навигацию в `src/components/AppShell.tsx`
6. Добавьте тесты в `src/pages/__tests__/`

Пример страницы:

```tsx
// src/pages/MyPage.tsx
import React from 'react'
import { Button } from '@/shadcn/ui/button'

const MyPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">My Page</h1>
      <p>This is my custom page</p>
      <Button>Click me</Button>
    </div>
  )
}

export default MyPage
```

## Управление состоянием

### Использование Zustand

Глобальное состояние управляется с помощью Zustand. Хранилище находится в `src/state/uiStore.ts`.

Пример использования:

```tsx
import { useUIStore } from '@/state/uiStore'

const MyComponent: React.FC = () => {
  const theme = useUIStore(state => state.theme)
  const setTheme = useUIStore(state => state.setTheme)

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }

  return (
    <div>
      <p>Current theme: {theme}</p>
      <button onClick={toggleTheme}>Toggle theme</button>
    </div>
  )
}
```

## Работа с API

### Использование API клиента

API клиент находится в `src/lib/api.ts`. Он предоставляет функции для работы с HTTP запросами.

Пример использования:

```tsx
import { get, post } from '@/lib/api'
import { Feature } from '@/lib/types'

const MyComponent: React.FC = () => {
  const [features, setFeatures] = React.useState<Feature[]>([])
  const [loading, setLoading] = React.useState(false)

  const loadFeatures = async () => {
    setLoading(true)
    try {
      const data = await get<Feature[]>('/orchestrator/features')
      setFeatures(data)
    } catch (error) {
      console.error('Failed to load features', error)
    } finally {
      setLoading(false)
    }
  }

  const createFeature = async (title: string) => {
    try {
      const newFeature = await post<Feature>('/orchestrator/features', { title })
      setFeatures([...features, newFeature])
    } catch (error) {
      console.error('Failed to create feature', error)
    }
  }

  React.useEffect(() => {
    loadFeatures()
  }, [])

  if (loading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      {features.map(feature => (
        <div key={feature.id}>{feature.title}</div>
      ))}
    </div>
  )
}
```

### Использование TanStack Query

Для управления состоянием запросов и кэширования используется TanStack Query.

Пример использования:

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post } from '@/lib/api'
import { Feature } from '@/lib/types'

const MyComponent: React.FC = () => {
  const queryClient = useQueryClient()

  const { data: features, isLoading, error } = useQuery<Feature[]>({
    queryKey: ['features'],
    queryFn: () => get<Feature[]>('/orchestrator/features')
  })

  const createFeatureMutation = useMutation({
    mutationFn: (title: string) => post<Feature>('/orchestrator/features', { title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['features'] })
    }
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error: {error.message}</div>
  }

  return (
    <div>
      {features?.map(feature => (
        <div key={feature.id}>{feature.title}</div>
      ))}
      <button onClick={() => createFeatureMutation.mutate('New Feature')}>
        Create Feature
      </button>
    </div>
  )
}
```

## Работа с потоками данных

### Использование Server-Sent Events

Для работы с Server-Sent Events используется клиент в `src/lib/sse.ts`.

Пример использования:

```tsx
import React from 'react'
import { sseClient } from '@/lib/sse'

const MyComponent: React.FC = () => {
  const [messages, setMessages] = React.useState<any[]>([])

  React.useEffect(() => {
    sseClient.connect('/stream/events')
    
    sseClient.on('job_started', (data) => {
      setMessages(prev => [...prev, { type: 'job_started', data }])
    })
    
    sseClient.on('job_finished', (data) => {
      setMessages(prev => [...prev, { type: 'job_finished', data }])
    })

    return () => {
      sseClient.disconnect()
    }
  }, [])

  return (
    <div>
      {messages.map((msg, index) => (
        <div key={index}>
          {msg.type}: {JSON.stringify(msg.data)}
        </div>
      ))}
    </div>
  )
}
```

## Стилизация

### Использование Tailwind CSS

Проект использует Tailwind CSS для стилизации. Используйте классы Tailwind напрямую в JSX:

```tsx
<div className="p-4 bg-white rounded-lg shadow">
  <h2 className="text-xl font-bold text-gray-800">Title</h2>
  <p className="mt-2 text-gray-600">Content</p>
</div>
```

### Темизация

Поддерживается светлая и темная тема. Используйте классы Tailwind с префиксами `dark:` для темной темы:

```tsx
<div className="bg-white dark:bg-gray-800 text-gray-900 dark:text-white">
  Content
</div>
```

## Тестирование

### Запуск тестов

```bash
cd /opt/feature-factory/app/ui
npm test
```

### Запуск тестов в режиме watch

```bash
cd /opt/feature-factory/app/ui
npm test -- --watch
```

### Запуск тестов с coverage отчетом

```bash
cd /opt/feature-factory/app/ui
npm test -- --coverage
```

### Написание тестов

Используйте React Testing Library для написания тестов компонентов:

```tsx
// src/components/__tests__/MyComponent.test.tsx
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import MyComponent from '@/components/MyComponent'

describe('MyComponent', () => {
  it('renders title', () => {
    render(<MyComponent title="Test Title" />)
    expect(screen.getByText('Test Title')).toBeInTheDocument()
  })

  it('calls onClick when button is clicked', () => {
    const handleClick = jest.fn()
    render(<MyComponent title="Test Title" onClick={handleClick} />)
    
    const button = screen.getByRole('button')
    fireEvent.click(button)
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

## Линтинг и форматирование

### ESLint

Проект использует ESLint для проверки кода. Конфигурация находится в `.eslintrc.json`.

### Prettier

Проект использует Prettier для форматирования кода. Конфигурация находится в `.prettierrc`.

### Автоматическое форматирование при сохранении

Настройте ваш редактор для автоматического форматирования кода при сохранении с помощью Prettier.

## Деплой

### Сборка проекта

```bash
cd /opt/feature-factory/app/ui
npm run build
```

### Деплой через скрипт

Используйте скрипт деплоя:

```bash
sudo /opt/feature-factory/scripts/deploy_ui.sh
```

## Best Practices

### Компоненты

1. **Делайте компоненты небольшими и переиспользуемыми**
2. **Используйте TypeScript для типизации**
3. **Пишите тесты для критических компонентов**
4. **Используйте React Hooks вместо классовых компонентов**
5. **Избегайте пропс-дрilling, используйте Zustand для глобального состояния**

### Стилизация

1. **Используйте Tailwind CSS классы вместо CSS модулей**
2. **Следуйте принципам мобильного первого дизайна**
3. **Поддерживайте темную тему**
4. **Используйте семантические HTML теги**

### Производительность

1. **Используйте React.memo для мемоизации компонентов**
2. **Используйте useMemo и useCallback для мемоизации значений и функций**
3. **Ленивая загрузка компонентов с помощью React.lazy**
4. **Используйте виртуализацию списков для больших наборов данных**

### Безопасность

1. **Всегда валидируйте входные данные**
2. **Используйте HTTPS для всех запросов**
3. **Санитизируйте данные перед отображением**
4. **Избегайте использования dangerouslySetInnerHTML**

### Доступность

1. **Используйте семантические HTML теги**
2. **Предоставляйте альтернативный текст для изображений**
3. **Используйте ARIA атрибуты при необходимости**
4. **Обеспечьте навигацию с клавиатуры**

## Troubleshooting

### Проблемы с зависимостями

Если возникают проблемы с зависимостями:

```bash
cd /opt/feature-factory/app/ui
rm -rf node_modules package-lock.json
npm install
```

### Проблемы с типизацией

Если TypeScript ругается на типы:

1. Проверьте правильность типов
2. Убедитесь, что все зависимости установлены
3. Попробуйте перезапустить TypeScript сервер

### Проблемы с линтингом

Если ESLint ругается:

```bash
cd /opt/feature-factory/app/ui
npm run lint:fix
```

### Проблемы с тестами

Если тесты не проходят:

1. Проверьте, что компоненты правильно рендерятся
2. Убедитесь, что моки настроены правильно
3. Проверьте, что тесты покрывают все кейсы

## Полезные ссылки

- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [React Testing Library Documentation](https://testing-library.com/docs/react-testing-library/intro/)
- [Vite Documentation](https://vitejs.dev/guide/)