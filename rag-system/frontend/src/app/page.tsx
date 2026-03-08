'use client'

import { useState, useEffect } from 'react'
import { Settings } from '@/components/Settings'
import { FileUpload } from '@/components/FileUpload'
import { Chat } from '@/components/Chat'
import { DatabaseInfo } from '@/components/DatabaseInfo'
import { api } from '@/lib/api'
import { AlertCircle, BookOpen } from 'lucide-react'

export interface AppSettings {
  // Retrieval
  bm25Weight: number
  semanticWeight: number
  topK: number
  relevanceThreshold: number
  enableReranking: boolean
  enableQueryRewriting: boolean
  // Chunking
  chunkSize: number
  chunkOverlap: number
  enableSemanticChunking: boolean
  // LLM
  llmModel: string
  embeddingModel: string
  temperature: number
  maxTokens: number
  // Collection
  collection: string
}

const defaultSettings: AppSettings = {
  bm25Weight: 0.15,
  semanticWeight: 0.85,
  topK: 5,
  relevanceThreshold: 0.3,
  enableReranking: true,
  enableQueryRewriting: true,
  chunkSize: 800,
  chunkOverlap: 200,
  enableSemanticChunking: true,
  llmModel: 'llama3.1',
  embeddingModel: 'BAAI/bge-m3',
  temperature: 0.1,
  maxTokens: 2048,
  collection: 'default',
}

export default function Home() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings)
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  useEffect(() => {
    checkApiHealth()
  }, [])

  const checkApiHealth = async () => {
    try {
      await api.get('/api/health')
      setApiHealthy(true)
    } catch {
      setApiHealthy(false)
    }
  }

  const triggerRefresh = () => {
    setRefreshTrigger(prev => prev + 1)
  }

  if (apiHealthy === null) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!apiHealthy) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="card max-w-md text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Backend API Unavailable</h2>
          <p className="text-gray-600 mb-4">
            Please ensure the backend server is running at http://127.0.0.1:8001
          </p>
          <code className="block bg-gray-100 p-3 rounded-lg text-sm text-left mb-4">
            cd backend && uvicorn app.main:app --reload
          </code>
          <button onClick={checkApiHealth} className="btn-primary">
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8 text-primary-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">RAG Document Q&A System</h1>
              <p className="text-sm text-gray-500">
                Upload documents and ask questions to get answers based on your contracts and documents
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Sidebar */}
          <div className="space-y-6">
            <Settings settings={settings} setSettings={setSettings} />
            <FileUpload settings={settings} onUploadComplete={triggerRefresh} />
            <DatabaseInfo refreshTrigger={refreshTrigger} collection={settings.collection} />
          </div>

          {/* Main Chat Area */}
          <div className="lg:col-span-2">
            <Chat settings={settings} />
          </div>
        </div>
      </div>
    </main>
  )
}
