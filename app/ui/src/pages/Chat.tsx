import React from 'react'
import MaintainerChat from '@/components/MaintainerChat'

const Chat: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Chat (Product)</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Диалог с Product для сбора требований и запуска фич. Секреты передавайте через безопасную форму.
        </p>
      </div>
      
      <MaintainerChat />
    </div>
  )
}

export default Chat
