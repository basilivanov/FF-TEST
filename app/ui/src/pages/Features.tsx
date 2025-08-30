import React from 'react'
import FeatureList from '@/components/FeatureList'

const Features: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Features</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Список фич
        </p>
      </div>

      <FeatureList />
    </div>
  )
}

export default Features