'use client'

import { useState, useEffect } from 'react'
import { Database, RefreshCw, FileText, Layers, HardDrive, FolderOpen, AlertCircle } from 'lucide-react'
import { fetchIngestStats, DatabaseStats, getErrorMessage } from '@/lib/api'

interface DatabaseInfoProps {
  refreshTrigger: number
  collection: string
}

export function DatabaseInfo({ refreshTrigger, collection }: DatabaseInfoProps) {
  const [stats, setStats] = useState<DatabaseStats | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
  }, [refreshTrigger, collection])

  const loadStats = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchIngestStats()
      setStats(data)
    } catch (err) {
      const errorMsg = getErrorMessage(err)
      console.error('Error loading stats:', errorMsg)
      setError(errorMsg)
    }
    setIsLoading(false)
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-semibold">Database Info</h2>
        </div>
        <button
          onClick={loadStats}
          disabled={isLoading}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {stats ? (
        <div className="grid grid-cols-2 gap-4">
          <StatCard
            icon={<FileText className="w-5 h-5" />}
            value={stats.total_documents}
            label="Documents"
          />
          <StatCard
            icon={<Layers className="w-5 h-5" />}
            value={stats.total_chunks}
            label="Pages"
          />
          <StatCard
            icon={<FolderOpen className="w-5 h-5" />}
            value={stats.collections.length}
            label="Collections"
          />
          <StatCard
            icon={<HardDrive className="w-5 h-5" />}
            value={`${stats.storage_size_mb.toFixed(2)}`}
            label="MB Storage"
          />
        </div>
      ) : !error ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      ) : null}

      {/* Collections List */}
      {stats && stats.collections.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Collections</h3>
          <div className="flex flex-wrap gap-2">
            {stats.collections.map((col) => (
              <span
                key={col}
                className={`text-xs px-2 py-1 rounded-full ${
                  col === collection
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {col}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({
  icon,
  value,
  label,
}: {
  icon: React.ReactNode
  value: number | string
  label: string
}) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <div className="flex items-center justify-center text-primary-600 mb-1">{icon}</div>
      <div className="text-xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}
