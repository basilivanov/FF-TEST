import React from 'react'
import RunHistory from '@/components/RunHistory'

const Runs: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Runs</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          История запусков графов
        </p>
      </div>

      <RunHistory />
    </div>
  )
}

export default Runs