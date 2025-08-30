import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Интерфейс состояния UI
interface UIState {
  // Тема (светлая/темная)
  theme: 'light' | 'dark'
  setTheme: (theme: 'light' | 'dark') => void
  
  // Состояние боковой панели
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  
  // Тип аналитика для чата
  analystType: 'INTERNAL' | 'BUSINESS'
  setAnalystType: (type: 'INTERNAL' | 'BUSINESS') => void
  
  // Фильтры для страниц
  featureFilters: {
    status: string[]
    priority: number | null
  }
  setFeatureFilters: (filters: Partial<UIState['featureFilters']>) => void
  resetFeatureFilters: () => void
  
  taskFilters: {
    role: string | null
    status: string[]
  }
  setTaskFilters: (filters: Partial<UIState['taskFilters']>) => void
  resetTaskFilters: () => void
  
  logFilters: {
    component: string | null
    level: string | null
    event: string | null
    agentRole: string | null
  }
  setLogFilters: (filters: Partial<UIState['logFilters']>) => void
  resetLogFilters: () => void
}

// Начальное состояние
const initialState = {
  theme: 'light' as const,
  sidebarCollapsed: false,
  analystType: 'BUSINESS' as const,
  featureFilters: {
    status: [],
    priority: null,
  },
  taskFilters: {
    role: null,
    status: [],
  },
  logFilters: {
    component: null,
    level: null,
    event: null,
    agentRole: null,
  },
}

// Создание хранилища Zustand с персистентностью
export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      // Установка темы
      setTheme: (theme) => set({ theme }),
      
      // Переключение состояния боковой панели
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      
      // Установка типа аналитика
      setAnalystType: (analystType) => set({ analystType }),
      
      // Управление фильтрами фич
      setFeatureFilters: (filters) => 
        set((state) => ({ 
          featureFilters: { 
            ...state.featureFilters, 
            ...filters 
          } 
        })),
      resetFeatureFilters: () => 
        set({ featureFilters: initialState.featureFilters }),
      
      // Управление фильтрами задач
      setTaskFilters: (filters) => 
        set((state) => ({ 
          taskFilters: { 
            ...state.taskFilters, 
            ...filters 
          } 
        })),
      resetTaskFilters: () => 
        set({ taskFilters: initialState.taskFilters }),
      
      // Управление фильтрами логов
      setLogFilters: (filters) => 
        set((state) => ({ 
          logFilters: { 
            ...state.logFilters, 
            ...filters 
          } 
        })),
      resetLogFilters: () => 
        set({ logFilters: initialState.logFilters }),
    }),
    {
      name: 'ui-storage', // имя в localStorage
      partialize: (state) => ({ 
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        analystType: state.analystType,
        featureFilters: state.featureFilters,
        taskFilters: state.taskFilters,
      }), // сохраняем только часть состояния
    }
  )
)
