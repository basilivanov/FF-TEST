import React from 'react'
import TaskQueue from '@/components/TaskQueue'

const Queue: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Queue</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Очередь задач, ожидающих выполнения
        </p>
      </div>

      <TaskQueue />
    </div>
  )
}

export default Queue