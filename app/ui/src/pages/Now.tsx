import React from 'react'
import RunningTasks from '@/components/RunningTasks'

const Now: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Now</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Текущие выполняющиеся задачи и последние события системы
        </p>
      </div>

      <RunningTasks />
    </div>
  )
}

export default Now