'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, User, Bot, Clock, FileText, RefreshCw, Trash2, ChevronDown, ChevronUp } from 'lucide-react'
import { sendChatMessage, ChatResponse, Source } from '@/lib/api'
import type { AppSettings } from '@/app/page'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  rewrittenQuery?: string
  processingTime?: number
}

interface ChatProps {
  settings: AppSettings
}

export function Chat({ settings }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)

    try {
      const response: ChatResponse = await sendChatMessage({
        query: userMessage,
        collection: settings.collection,
        embedding_model: settings.embeddingModel,
        llm_model: settings.llmModel,
        temperature: settings.temperature,
        max_tokens: settings.maxTokens,
        bm25_weight: settings.bm25Weight,
        semantic_weight: settings.semanticWeight,
        top_k: settings.topK,
        relevance_threshold: settings.relevanceThreshold,
        enable_reranking: settings.enableReranking,
        enable_query_rewriting: settings.enableQueryRewriting,
      })

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
          rewrittenQuery: response.rewritten_query || undefined,
          processingTime: response.processing_time,
        },
      ])
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, there was an error processing your request. Please try again.',
        },
      ])
    }

    setIsLoading(false)
  }

  const clearChat = () => {
    setMessages([])
  }

  return (
    <div className="card h-[calc(100vh-180px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-4 border-b">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-primary-600" />
          <h2 className="text-lg font-semibold">Ask Questions</h2>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-red-500 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-gray-500">
            <Bot className="w-16 h-16 mb-4 text-gray-300" />
            <p className="text-lg font-medium">Start a Conversation</p>
            <p className="text-sm mt-1">Ask questions about your uploaded documents</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))
        )}

        {isLoading && (
          <div className="flex items-start gap-3 message-animation">
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
              <Bot className="w-5 h-5 text-primary-600" />
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600" />
                <span className="text-sm text-gray-600">Searching documents...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your documents..."
          className="input-field flex-1"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="btn-primary flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
          Send
        </button>
      </form>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const [showSources, setShowSources] = useState(false)
  const isUser = message.role === 'user'

  return (
    <div className={`flex items-start gap-3 message-animation ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? 'bg-primary-600' : 'bg-primary-100'
        }`}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-primary-600" />
        )}
      </div>

      <div className={`max-w-[80%] ${isUser ? 'text-right' : ''}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary-600 text-white rounded-tr-none'
              : 'bg-gray-100 text-gray-900 rounded-tl-none'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Metadata for assistant messages */}
        {!isUser && (
          <div className="mt-2 space-y-2">
            {/* Processing time and rewritten query */}
            <div className="flex items-center gap-3 text-xs text-gray-500">
              {message.processingTime && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {message.processingTime.toFixed(2)}s
                </span>
              )}
              {message.rewrittenQuery && (
                <span className="flex items-center gap-1">
                  <RefreshCw className="w-3 h-3" />
                  Rewritten
                </span>
              )}
            </div>

            {/* Sources toggle */}
            {message.sources && message.sources.length > 0 && (
              <div>
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
                >
                  <FileText className="w-4 h-4" />
                  {message.sources.length} Sources
                  {showSources ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>

                {showSources && (
                  <div className="mt-2 space-y-2">
                    {message.sources.map((source, idx) => (
                      <SourceCard key={idx} source={source} index={idx} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function SourceCard({ source, index }: { source: Source; index: number }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3 text-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-gray-900">
          {index + 1}. {source.filename}
        </span>
        {source.page && (
          <span className="text-xs text-gray-500">Page {source.page}</span>
        )}
      </div>

      {/* Relevance score */}
      <div className="mb-2">
        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
          <span>Relevance</span>
          <span>{(source.score * 100).toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1.5">
          <div
            className="bg-primary-600 h-1.5 rounded-full transition-all"
            style={{ width: `${Math.min(source.score * 100, 100)}%` }}
          />
        </div>
      </div>

      {/* Text snippet */}
      <p className="text-gray-600 text-xs line-clamp-3">{source.text}</p>
    </div>
  )
}
