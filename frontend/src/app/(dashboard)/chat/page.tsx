'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Send, FileText, Loader2, X, Brain, Search, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { useAuthStore } from '@/store/auth'
import { sendChatMessage, ChatMessage } from '@/lib/api'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface SelectedDocument {
  id: string
  title: string
}

interface SearchResult {
  id: string
  title: string
  source: string
  year: number | null
}

export default function ChatPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { accessToken } = useAuthStore()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'all' | 'single' | 'minister'>('all')
  const [selectedDocument, setSelectedDocument] = useState<SelectedDocument | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // Document search state
  const [docSearchOpen, setDocSearchOpen] = useState(false)
  const [docSearchQuery, setDocSearchQuery] = useState('')
  const [docSearchResults, setDocSearchResults] = useState<SearchResult[]>([])
  const [docSearchLoading, setDocSearchLoading] = useState(false)

  // Debounced document search
  const searchDocuments = useCallback(async (query: string) => {
    if (!query.trim()) {
      setDocSearchResults([])
      return
    }
    
    setDocSearchLoading(true)
    try {
      const res = await fetch(`${API_URL}/test/reports?search=${encodeURIComponent(query)}&limit=10`)
      const data = await res.json()
      setDocSearchResults(
        (data.items || []).map((r: any) => ({
          id: r.id,
          title: r.title,
          source: r.source,
          year: r.year
        }))
      )
    } catch (err) {
      setDocSearchResults([])
    } finally {
      setDocSearchLoading(false)
    }
  }, [])

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (docSearchQuery) {
        searchDocuments(docSearchQuery)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [docSearchQuery, searchDocuments])

  const selectDocument = (doc: SearchResult) => {
    setSelectedDocument({ id: doc.id, title: doc.title })
    setMode('single')
    setDocSearchOpen(false)
    setDocSearchQuery('')
    setDocSearchResults([])
  }

  // Handle document query parameter for single-document chat
  useEffect(() => {
    const documentId = searchParams.get('document')
    if (documentId) {
      fetch(`${API_URL}/test/reports/${documentId}`)
        .then(res => res.json())
        .then(data => {
          if (data && !data.error) {
            setSelectedDocument({
              id: documentId,
              title: data.title?.substring(0, 100) || 'Selected Report'
            })
            setMode('single')
          }
        })
        .catch(() => {
          setSelectedDocument({ id: documentId, title: 'Selected Report' })
          setMode('single')
        })
    }
  }, [searchParams])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const documentId = mode === 'single' && selectedDocument ? selectedDocument.id : undefined
      const response = await sendChatMessage(input, mode, documentId, accessToken || undefined)
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        citations: response.citations,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Error: ${error.message || 'Failed to get response'}`,
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const clearSelectedDocument = () => {
    setSelectedDocument(null)
    setMode('all')
    router.push('/chat')
  }

  return (
    <div className="flex flex-col h-full">
      {/* Mode Selector */}
      <div className="flex items-center gap-2 p-4 border-b flex-wrap">
        <span className="text-sm font-medium text-muted-foreground mr-2">Mode:</span>
        <Button
          variant={mode === 'all' && !selectedDocument ? 'default' : 'outline'}
          size="sm"
          onClick={() => {
            setMode('all')
            clearSelectedDocument()
          }}
        >
          All Reports
        </Button>
        
        {/* Document Search Selector */}
        {selectedDocument ? (
          <Button
            variant={mode === 'single' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setMode('single')}
            className="max-w-xs"
          >
            <FileText className="h-4 w-4 mr-1" />
            <span className="truncate max-w-[150px]">{selectedDocument.title}</span>
            <X 
              className="h-3 w-3 ml-2 hover:text-destructive" 
              onClick={(e) => {
                e.stopPropagation()
                clearSelectedDocument()
              }}
            />
          </Button>
        ) : (
          <Popover open={docSearchOpen} onOpenChange={setDocSearchOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" size="sm">
                <Plus className="h-4 w-4 mr-1" />
                Select Document
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[400px] p-0" align="start">
              <Command shouldFilter={false}>
                <CommandInput
                  placeholder="Search reports..."
                  value={docSearchQuery}
                  onValueChange={setDocSearchQuery}
                />
                <CommandList>
                  {docSearchLoading && (
                    <div className="py-6 text-center text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin mx-auto mb-2" />
                      Searching...
                    </div>
                  )}
                  {!docSearchLoading && docSearchQuery && docSearchResults.length === 0 && (
                    <CommandEmpty>No reports found.</CommandEmpty>
                  )}
                  {!docSearchLoading && !docSearchQuery && (
                    <div className="py-6 text-center text-sm text-muted-foreground">
                      <Search className="h-4 w-4 mx-auto mb-2 opacity-50" />
                      Type to search reports...
                    </div>
                  )}
                  {docSearchResults.length > 0 && (
                    <CommandGroup heading="Reports">
                      {docSearchResults.map((doc) => (
                        <CommandItem
                          key={doc.id}
                          value={doc.id}
                          onSelect={() => selectDocument(doc)}
                          className="cursor-pointer"
                        >
                          <FileText className="h-4 w-4 mr-2 text-muted-foreground" />
                          <div className="flex-1 truncate">
                            <p className="truncate text-sm">{doc.title}</p>
                            <p className="text-xs text-muted-foreground">
                              {doc.source !== 'Unknown' && doc.source}
                              {doc.source !== 'Unknown' && doc.year && ' · '}
                              {doc.year}
                            </p>
                          </div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  )}
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        )}
        
        <Button
          variant={mode === 'minister' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setMode('minister')}
        >
          <Brain className="h-4 w-4 mr-1" />
          Digital Minister
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">
              {selectedDocument ? 'Chat with this Report' : 'Chat with Intelligence Hub'}
            </h2>
            {selectedDocument ? (
              <div className="max-w-lg">
                <p className="text-muted-foreground text-sm mb-2">
                  Chatting with:
                </p>
                <p className="text-sm font-medium px-4 py-2 bg-primary/10 rounded-lg mb-4">
                  {selectedDocument.title}
                </p>
              </div>
            ) : (
              <p className="text-muted-foreground max-w-md">
                Ask questions about AI governance, technology trends, and insights from strategic reports.
              </p>
            )}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-2 max-w-2xl">
              {(selectedDocument ? [
                'Summarize the key findings',
                'What are the main recommendations?',
                'What statistics are mentioned?',
                'What are the key risks identified?',
              ] : [
                'What are the key AI governance recommendations?',
                'Compare AI adoption rates across industries',
                'What are the main risks of generative AI?',
                'Summarize UAE AI strategy initiatives',
              ]).map((suggestion) => (
                <Button
                  key={suggestion}
                  variant="outline"
                  className="text-left h-auto py-2 px-3"
                  onClick={() => setInput(suggestion)}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <Card
              className={`max-w-3xl p-4 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
              {message.citations && message.citations.length > 0 && (
                <div className="mt-4 pt-4 border-t border-border/50">
                  <p className="text-xs font-medium mb-2">Sources:</p>
                  <div className="space-y-2">
                    {message.citations.slice(0, 5).map((citation, i) => (
                      <div
                        key={i}
                        className="text-xs p-2 rounded bg-background/50"
                      >
                        <span className="font-medium">{citation.source}</span>
                        <span className="text-muted-foreground ml-2">
                          (relevance: {(citation.score * 100).toFixed(0)}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <Card className="p-4 bg-muted">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Analyzing reports...</span>
              </div>
            </Card>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about AI governance, trends, statistics..."
            disabled={loading}
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={loading || !input.trim()}>
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  )
}
