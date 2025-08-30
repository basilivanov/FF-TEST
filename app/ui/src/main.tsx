import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import App from './App'
import './app.css'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

console.info('[FF/UI] Boot starting…')

// Определяем базовый префикс для роутинга: в проде под /admin, локально — /
const detectBaseName = () => {
  try {
    const p = window.location.pathname || '/'
    return p.startsWith('/admin') ? '/admin' : '/'
  } catch {
    return '/'
  }
}
const basename = detectBaseName()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter basename={basename}>
      <QueryClientProvider client={queryClient}>
        <App />
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
console.info('[FF/UI] Boot rendered root')
