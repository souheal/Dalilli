'use client'

import { useState, useEffect } from 'react'
import { Settings as SettingsIcon, Sliders, Scissors, Brain, FolderOpen, Plus } from 'lucide-react'
import { fetchCollections, fetchEmbeddingModels, fetchLLMModels, createCollection, Collection } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { AppSettings } from '@/app/page'

interface SettingsProps {
  settings: AppSettings
  setSettings: (settings: AppSettings) => void
}

type TabType = 'retrieval' | 'chunking' | 'llm' | 'collections'

export function Settings({ settings, setSettings }: SettingsProps) {
  const [activeTab, setActiveTab] = useState<TabType>('retrieval')
  const [collections, setCollections] = useState<Collection[]>([])
  const [embeddingModels, setEmbeddingModels] = useState<string[]>(['BAAI/bge-m3', 'intfloat/multilingual-e5-large'])
  const [llmModels, setLlmModels] = useState<string[]>(['llama3.1'])
  const [newCollectionName, setNewCollectionName] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [collectionsData, embeddingData, llmData] = await Promise.all([
        fetchCollections(),
        fetchEmbeddingModels().catch(() => embeddingModels),
        fetchLLMModels().catch(() => llmModels),
      ])
      setCollections(collectionsData)
      setEmbeddingModels(embeddingData)
      setLlmModels(llmData)
    } catch (error) {
      console.error('Error loading settings data:', error)
    }
  }

  const handleCreateCollection = async () => {
    if (!newCollectionName.trim()) return
    setIsCreating(true)
    try {
      await createCollection(newCollectionName.trim())
      setNewCollectionName('')
      await loadData()
    } catch (error) {
      console.error('Error creating collection:', error)
    }
    setIsCreating(false)
  }

  const tabs: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: 'retrieval', label: 'Retrieval', icon: <Sliders className="w-4 h-4" /> },
    { id: 'chunking', label: 'Chunking', icon: <Scissors className="w-4 h-4" /> },
    { id: 'llm', label: 'LLM', icon: <Brain className="w-4 h-4" /> },
    { id: 'collections', label: 'Collections', icon: <FolderOpen className="w-4 h-4" /> },
  ]

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <SettingsIcon className="w-5 h-5 text-primary-600" />
        <h2 className="text-lg font-semibold">Settings</h2>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'tab-button flex items-center gap-1.5 whitespace-nowrap',
              activeTab === tab.id ? 'tab-button-active' : 'tab-button-inactive'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="space-y-4">
        {activeTab === 'retrieval' && (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">BM25 Weight</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.bm25Weight}
                  onChange={(e) => setSettings({ ...settings, bm25Weight: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <span className="text-sm text-gray-500">{settings.bm25Weight}</span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Semantic Weight</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.semanticWeight}
                  onChange={(e) => setSettings({ ...settings, semanticWeight: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <span className="text-sm text-gray-500">{settings.semanticWeight}</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Top-K Results: {settings.topK}</label>
              <input
                type="range"
                min="1"
                max="20"
                value={settings.topK}
                onChange={(e) => setSettings({ ...settings, topK: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Relevance Threshold: {settings.relevanceThreshold}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.relevanceThreshold}
                onChange={(e) => setSettings({ ...settings, relevanceThreshold: parseFloat(e.target.value) })}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.enableReranking}
                  onChange={(e) => setSettings({ ...settings, enableReranking: e.target.checked })}
                  className="rounded text-primary-600"
                />
                <span className="text-sm">Enable Re-ranking</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.enableQueryRewriting}
                  onChange={(e) => setSettings({ ...settings, enableQueryRewriting: e.target.checked })}
                  className="rounded text-primary-600"
                />
                <span className="text-sm">Enable Query Rewriting</span>
              </label>
            </div>
          </>
        )}

        {activeTab === 'chunking' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Chunk Size: {settings.chunkSize} tokens
              </label>
              <input
                type="range"
                min="100"
                max="2000"
                step="100"
                value={settings.chunkSize}
                onChange={(e) => setSettings({ ...settings, chunkSize: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Chunk Overlap: {settings.chunkOverlap} tokens
              </label>
              <input
                type="range"
                min="0"
                max="500"
                step="50"
                value={settings.chunkOverlap}
                onChange={(e) => setSettings({ ...settings, chunkOverlap: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.enableSemanticChunking}
                onChange={(e) => setSettings({ ...settings, enableSemanticChunking: e.target.checked })}
                className="rounded text-primary-600"
              />
              <span className="text-sm">Enable Semantic Chunking</span>
            </label>
          </>
        )}

        {activeTab === 'llm' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">LLM Model</label>
              <select
                value={settings.llmModel}
                onChange={(e) => setSettings({ ...settings, llmModel: e.target.value })}
                className="input-field"
              >
                {llmModels.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Embedding Model</label>
              <select
                value={settings.embeddingModel}
                onChange={(e) => setSettings({ ...settings, embeddingModel: e.target.value })}
                className="input-field"
              >
                {embeddingModels.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Temperature: {settings.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Tokens: {settings.maxTokens}
              </label>
              <input
                type="range"
                min="256"
                max="8192"
                step="256"
                value={settings.maxTokens}
                onChange={(e) => setSettings({ ...settings, maxTokens: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>
          </>
        )}

        {activeTab === 'collections' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Active Collection</label>
              <select
                value={settings.collection}
                onChange={(e) => setSettings({ ...settings, collection: e.target.value })}
                className="input-field"
              >
                {collections.map((col) => (
                  <option key={col.name} value={col.name}>
                    {col.name} ({col.document_count} docs)
                  </option>
                ))}
                {collections.length === 0 && <option value="default">default</option>}
              </select>
            </div>

            <div className="border-t pt-4 mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Create New Collection</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                  placeholder="e.g., contracts-2024"
                  className="input-field flex-1"
                />
                <button
                  onClick={handleCreateCollection}
                  disabled={isCreating || !newCollectionName.trim()}
                  className="btn-primary flex items-center gap-1"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
