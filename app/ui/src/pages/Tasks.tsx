import React from 'react'
import TaskList from '@/components/TaskList'

const Tasks: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Tasks</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Список задач
        </p>
      </div>

      <TaskList />
    </div>
  )
}

export default Tasks