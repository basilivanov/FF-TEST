import React from 'react'
import ErrorList from '@/components/ErrorList'

const Errors: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Errors</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Последние ошибки и предупреждения системы
        </p>
      </div>

      <ErrorList />
    </div>
  )
}

export default Errors