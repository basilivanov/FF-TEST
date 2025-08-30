import React from 'react'
import FeatureDetailComponent from '@/components/FeatureDetail'
import { Link, useParams } from 'react-router-dom'
import { Button } from '@/shadcn/ui/button'
import { ArrowLeft } from 'lucide-react'

const FeatureDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  
  return (
    <div className="space-y-6">
      <div>
            <Link to="features" className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300">
          <ArrowLeft className="mr-1 h-4 w-4" />
          Назад к списку фич
        </Link>
        <div className="mt-2">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Детали фичи #{id}</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Детали фичи и управление её выполнением
          </p>
        </div>
      </div>
      
      <FeatureDetailComponent />
    </div>
  )
}

export default FeatureDetail
