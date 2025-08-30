import React, { useState } from 'react'
import { Button } from '@/shadcn/ui/button'
import { Input } from '@/shadcn/ui/input'
import { Textarea } from '@/shadcn/ui/textarea'
import { 
  Save, 
  RotateCcw,
  Key,
  Clock,
  Calendar,
  Edit
} from 'lucide-react'

const Settings: React.FC = () => {
  const [settings, setSettings] = useState({
    app_tz: 'Europe/Moscow',
    schedules: {
      etl_daily: '0 2 * * *',
      backup_weekly: '0 3 * * 0',
      cleanup_monthly: '0 4 1 * *'
    },
    api_keys: {
      openai: 'sk-***',
      anthropic: 'sk-ant-***',
      gemini: 'AIza***'
    },
    ids: {
      project_id: 'ff-mvp-2025',
      cluster_id: 'ff-cluster-test',
      region: 'eu-west-1'
    }
  })
  
  const [isEditing, setIsEditing] = useState(false)
  
  // Handle input changes
  const handleChange = (field: string, value: string) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }))
  }
  
  // Handle nested object changes
  const handleNestedChange = (parent: string, field: string, value: string) => {
    setSettings(prev => ({
      ...prev,
      [parent]: {
        ...prev[parent as keyof typeof settings],
        [field]: value
      }
    }))
  }
  
  // Save settings
  const saveSettings = () => {
    // In a real implementation, this would send the settings to the backend
    console.log('Saving settings:', settings)
    setIsEditing(false)
  }
  
  // Reset settings to default
  const resetSettings = () => {
    // In a real implementation, this would reset to default values
    console.log('Resetting settings to default')
    setSettings({
      app_tz: 'Europe/Moscow',
      schedules: {
        etl_daily: '0 2 * * *',
        backup_weekly: '0 3 * * 0',
        cleanup_monthly: '0 4 1 * *'
      },
      api_keys: {
        openai: 'sk-***',
        anthropic: 'sk-ant-***',
        gemini: 'AIza***'
      },
      ids: {
        project_id: 'ff-mvp-2025',
        cluster_id: 'ff-cluster-test',
        region: 'eu-west-1'
      }
    })
    setIsEditing(false)
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Настройки системы (только чтение в MVP)
        </p>
      </div>

      {/* Actions */}
      <div className="flex space-x-2">
        <Button onClick={() => setIsEditing(true)} disabled={isEditing}>
          <Edit className="mr-2 h-4 w-4" />
          Редактировать
        </Button>
        <Button variant="outline" onClick={resetSettings}>
          <RotateCcw className="mr-2 h-4 w-4" />
          Сбросить
        </Button>
      </div>

      {/* Timezone Setting */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Часовой пояс приложения</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="app_tz" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              APP_TZ
            </label>
            <Input
              id="app_tz"
              value={settings.app_tz}
              onChange={(e) => handleChange('app_tz', e.target.value)}
              readOnly={!isEditing}
              className={isEditing ? '' : 'bg-gray-50 dark:bg-gray-700'}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Часовой пояс, используемый приложением по умолчанию
            </p>
          </div>
          <div className="flex items-center">
            <Clock className="h-5 w-5 text-gray-400 mr-2" />
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Текущее время: {new Date().toLocaleString('ru-RU', { timeZone: settings.app_tz })}
            </span>
          </div>
        </div>
      </div>

      {/* Schedules */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Расписания</h2>
        <div className="space-y-4">
          <div>
            <label htmlFor="etl_daily" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              ETL Daily
            </label>
            <Input
              id="etl_daily"
              value={settings.schedules.etl_daily}
              onChange={(e) => handleNestedChange('schedules', 'etl_daily', e.target.value)}
              readOnly={!isEditing}
              className={isEditing ? '' : 'bg-gray-50 dark:bg-gray-700'}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Ежедневный ETL процесс (cron выражение)
            </p>
          </div>
          
          <div>
            <label htmlFor="backup_weekly" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Backup Weekly
            </label>
            <Input
              id="backup_weekly"
              value={settings.schedules.backup_weekly}
              onChange={(e) => handleNestedChange('schedules', 'backup_weekly', e.target.value)}
              readOnly={!isEditing}
              className={isEditing ? '' : 'bg-gray-50 dark:bg-gray-700'}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Еженедельный бэкап (cron выражение)
            </p>
          </div>
          
          <div>
            <label htmlFor="cleanup_monthly" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Cleanup Monthly
            </label>
            <Input
              id="cleanup_monthly"
              value={settings.schedules.cleanup_monthly}
              onChange={(e) => handleNestedChange('schedules', 'cleanup_monthly', e.target.value)}
              readOnly={!isEditing}
              className={isEditing ? '' : 'bg-gray-50 dark:bg-gray-700'}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Ежемесячная очистка (cron выражение)
            </p>
          </div>
        </div>
      </div>

      {/* API Keys */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">API Keys</h2>
        <div className="space-y-4">
          <div>
            <label htmlFor="openai" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              OpenAI
            </label>
            <div className="flex items-center">
              <Key className="h-4 w-4 text-gray-400 mr-2" />
              <Input
                id="openai"
                value={settings.api_keys.openai}
                onChange={(e) => handleNestedChange('api_keys', 'openai', e.target.value)}
                readOnly={!isEditing}
                className={isEditing ? '' : 'bg-gray-50 dark:bg-gray-700'}
              />
            </div>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              API ключ для OpenAI
            </p>
          </div>
          
          <div>
            <label htmlFor="anthropic" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Anthropic
            </label>
            <div className="flex items-center">
              <Key className="h-4 w-4 text-gray-400 mr-2" />
              <Input
                id="anthropic"
                value={settings.api_keys.anthropic}
                onChange={(e) => handleNestedChange('api_keys', 'anthropic', e.target.value)}
                readOnly={!isEditing}
                className={isEditing ? '' : 'bg-gray-50 dark:bg-gray-700'}
              />
            </div>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              API ключ для Anthropic
            </p>
          </div>
          
          <div>
            <label htmlFor="gemini" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Gemini
            </label>
            <div className="flex items-center">
              <Key className="h-4 w-4 text-gray-400 mr-2" />
              <Input
                id="gemini"
                value={settings.api_keys.gemini}
                onChange={(e) => handleNestedChange('api_keys', 'gemini', e.target.value)}
                readOnly={!isEditing}
                className={isEditing ? '' : 'bg-gray-50 dark:bg-gray-700'}
              />
            </div>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              API ключ для Gemini
            </p>
          </div>
        </div>
      </div>

      {/* IDs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Идентификаторы</h2>
        <div className="space-y-4">
          <div>
            <label htmlFor="project_id" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Project ID
            </label>
            <Input
              id="project_id"
              value={settings.ids.project_id}
              onChange={(e) => handleNestedChange('ids', 'project_id', e.target.value)}
              readOnly={!isEditing}
              className={isEditing ? '' : 'bg-gray-50 dark:bg-gray-700'}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Идентификатор проекта
            </p>
          </div>
          
          <div>
            <label htmlFor="cluster_id" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Cluster ID
            </label>
            <Input
              id="cluster_id"
              value={settings.ids.cluster_id}
              onChange={(e) => handleNestedChange('ids', 'cluster_id', e.target.value)}
              readOnly={!isEditing}
              className={isEditing ? '' : 'bg-gray-50 dark:bg-gray-700'}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Идентификатор кластера
            </p>
          </div>
          
          <div>
            <label htmlFor="region" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Region
            </label>
            <Input
              id="region"
              value={settings.ids.region}
              onChange={(e) => handleNestedChange('ids', 'region', e.target.value)}
              readOnly={!isEditing}
              className={isEditing ? '' : 'bg-gray-50 dark:bg-gray-700'}
            />
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Регион развертывания
            </p>
          </div>
        </div>
      </div>

      {/* Action buttons when editing */}
      {isEditing && (
        <div className="flex justify-end space-x-2">
          <Button variant="outline" onClick={() => setIsEditing(false)}>
            Отменить
          </Button>
          <Button onClick={saveSettings}>
            <Save className="mr-2 h-4 w-4" />
            Сохранить изменения
          </Button>
        </div>
      )}
    </div>
  )
}

export default Settings
