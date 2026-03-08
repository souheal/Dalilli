'use client'

import { useState, useCallback, useEffect } from 'react'
import { Upload, File, Trash2, X, CheckCircle, AlertCircle, Info } from 'lucide-react'
import {
  uploadDocument,
  fetchDocuments,
  deleteDocument,
  getErrorMessage,
  Document
} from '@/lib/api'
import { formatFileSize, getFileIcon } from '@/lib/utils'
import type { AppSettings } from '@/app/page'

interface FileUploadProps {
  settings: AppSettings
  onUploadComplete: () => void
}

interface UploadStatus {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

// Extended file types support
const ALLOWED_EXTENSIONS = [
  '.pdf',
  '.txt',
  '.docx',
  '.xlsx',
  '.pptx',
  '.png',
  '.jpg',
  '.jpeg',
  '.json'
]

export function FileUpload({ settings, onUploadComplete }: FileUploadProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [totalDocs, setTotalDocs] = useState(0)
  const [uploadQueue, setUploadQueue] = useState<UploadStatus[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [enableOcr, setEnableOcr] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      setLoadError(null)
      const docs = await fetchDocuments()
      setDocuments(docs || [])
      setTotalDocs(docs?.length || 0)
    } catch (error) {
      const errorMsg = getErrorMessage(error)
      console.error('Error loading documents:', errorMsg)
      setLoadError(errorMsg)
    }
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    addFilesToQueue(files)
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files)
      addFilesToQueue(files)
    }
  }

  const addFilesToQueue = (files: File[]) => {
    const validFiles = files.filter((file) => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      return ALLOWED_EXTENSIONS.includes(ext)
    })

    const invalidFiles = files.filter((file) => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      return !ALLOWED_EXTENSIONS.includes(ext)
    })

    if (invalidFiles.length > 0) {
      console.warn('Skipped unsupported files:', invalidFiles.map(f => f.name))
    }

    const newUploads: UploadStatus[] = validFiles.map((file) => ({
      file,
      status: 'pending',
    }))

    setUploadQueue((prev) => [...prev, ...newUploads])
  }

  const removeFromQueue = (index: number) => {
    setUploadQueue((prev) => prev.filter((_, i) => i !== index))
  }

  const uploadFiles = async () => {
    setIsLoading(true)

    for (let i = 0; i < uploadQueue.length; i++) {
      const item = uploadQueue[i]
      if (item.status !== 'pending') continue

      setUploadQueue((prev) =>
        prev.map((p, idx) => (idx === i ? { ...p, status: 'uploading' } : p))
      )

      try {
        await uploadDocument(
          item.file,
          settings.collection,
          settings.chunkSize,
          settings.chunkOverlap,
          settings.embeddingModel,
          enableOcr
        )

        setUploadQueue((prev) =>
          prev.map((p, idx) => (idx === i ? { ...p, status: 'success' } : p))
        )
      } catch (error) {
        const errorMsg = getErrorMessage(error)
        console.error('Upload error:', errorMsg)

        setUploadQueue((prev) =>
          prev.map((p, idx) =>
            idx === i ? { ...p, status: 'error', error: errorMsg } : p
          )
        )
      }
    }

    setIsLoading(false)
    await loadDocuments()
    onUploadComplete()

    // Clear successful uploads after a delay
    setTimeout(() => {
      setUploadQueue((prev) => prev.filter((p) => p.status !== 'success'))
    }, 2000)
  }

  const handleDeleteDocument = async (docId: string) => {
    try {
      await deleteDocument(docId)
      await loadDocuments()
      onUploadComplete()
    } catch (error) {
      const errorMsg = getErrorMessage(error)
      console.error('Error deleting document:', errorMsg)
      alert(`Failed to delete: ${errorMsg}`)
    }
  }

  const pendingUploads = uploadQueue.filter((u) => u.status === 'pending').length

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Upload className="w-5 h-5 text-primary-600" />
        <h2 className="text-lg font-semibold">Upload Documents</h2>
      </div>

      {/* Connection Error */}
      {loadError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Connection Error</span>
          </div>
          <p className="text-xs text-red-600 mt-1">{loadError}</p>
        </div>
      )}

      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          isDragging
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <Upload className="w-10 h-10 text-gray-400 mx-auto mb-2" />
        <p className="text-sm text-gray-600 mb-2">Drag files here or</p>
        <label className="btn-secondary cursor-pointer inline-block">
          Browse Files
          <input
            type="file"
            multiple
            accept={ALLOWED_EXTENSIONS.join(',')}
            onChange={handleFileSelect}
            className="hidden"
          />
        </label>
        <p className="text-xs text-gray-500 mt-2">
          PDF, Word, Excel, PowerPoint, TXT, Images, JSON
        </p>
      </div>

      {/* Upload Options */}
      <div className="mt-4 space-y-2">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={enableOcr}
            onChange={(e) => setEnableOcr(e.target.checked)}
            className="rounded text-primary-600"
          />
          <span className="text-sm text-gray-600">Enable OCR for scanned documents & images</span>
        </label>
        {enableOcr && (
          <div className="flex items-start gap-2 p-2 bg-blue-50 rounded-lg">
            <Info className="w-4 h-4 text-blue-600 mt-0.5" />
            <p className="text-xs text-blue-700">
              OCR requires Tesseract to be installed on the server.
              Scanned PDFs and images will be processed for text extraction.
            </p>
          </div>
        )}
      </div>

      {/* Upload Queue */}
      {uploadQueue.length > 0 && (
        <div className="mt-4 space-y-2">
          {uploadQueue.map((item, index) => (
            <div
              key={index}
              className={`flex items-center gap-3 p-2 rounded-lg ${
                item.status === 'error' ? 'bg-red-50' : 'bg-gray-50'
              }`}
            >
              <File className="w-5 h-5 text-gray-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <span className="text-sm truncate block">{item.file.name}</span>
                {item.status === 'error' && item.error && (
                  <span className="text-xs text-red-600 block truncate">{item.error}</span>
                )}
              </div>
              <span className="text-xs text-gray-500 flex-shrink-0">
                {formatFileSize(item.file.size)}
              </span>
              {item.status === 'pending' && (
                <button
                  onClick={() => removeFromQueue(index)}
                  className="p-1 hover:bg-gray-200 rounded flex-shrink-0"
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              )}
              {item.status === 'uploading' && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 flex-shrink-0" />
              )}
              {item.status === 'success' && (
                <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
              )}
              {item.status === 'error' && (
                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
              )}
            </div>
          ))}

          {pendingUploads > 0 && (
            <button
              onClick={uploadFiles}
              disabled={isLoading}
              className="btn-primary w-full mt-2"
            >
              {isLoading ? 'Uploading...' : `Upload ${pendingUploads} file(s)`}
            </button>
          )}
        </div>
      )}

      {/* Document List */}
      {documents.length > 0 && (
        <div className="mt-4 border-t pt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">
            Stored Documents ({totalDocs})
          </h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg group"
              >
                <span className="text-lg">{getFileIcon(doc.file_type || 'file')}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{doc.filename || doc.original_filename}</p>
                  <p className="text-xs text-gray-500">
                    {doc.num_chunks || doc.page_count || 0} chunk(s) • {formatFileSize(doc.size_bytes)}
                  </p>
                </div>
                <button
                  onClick={() => handleDeleteDocument(doc.id)}
                  className="p-1 opacity-0 group-hover:opacity-100 hover:bg-red-100 rounded transition-opacity"
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
