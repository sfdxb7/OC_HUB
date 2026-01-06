'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  History, 
  MessageSquare, 
  Search,
  Trash2,
  Calendar,
  FileText,
  Loader2,
  RefreshCw
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/store/auth'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Conversation {
  id: string
  title: string | null
  mode: string
  report_id: string | null
  message_count: number
  created_at: string
  updated_at: string
  reports?: { title: string } | null
}

export default function HistoryPage() {
  const router = useRouter()
  const { accessToken, user } = useAuthStore()
  const [search, setSearch] = useState('')
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const fetchConversations = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Try the test endpoint first (no auth required during development)
      const userId = user?.id || 'c496f932-a855-4690-825c-a9f52637f6df'
      const response = await fetch(`${API_URL}/test/conversations?user_id=${userId}`)
      
      if (!response.ok) {
        // Fallback to authenticated endpoint
        const authResponse = await fetch(`${API_URL}/api/chat/conversations`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        })
        
        if (!authResponse.ok) {
          throw new Error('Failed to fetch conversations')
        }
        
        const data = await authResponse.json()
        setConversations(data.conversations || data || [])
      } else {
        const data = await response.json()
        setConversations(data.conversations || [])
      }
    } catch (err: any) {
      console.error('Error fetching conversations:', err)
      setError(err.message || 'Failed to load conversations')
      setConversations([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConversations()
  }, [accessToken, user])

  const handleDelete = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return
    }
    
    setDeletingId(conversationId)
    
    try {
      const userId = user?.id || 'c496f932-a855-4690-825c-a9f52637f6df'
      const response = await fetch(
        `${API_URL}/test/conversations/${conversationId}?user_id=${userId}`,
        { method: 'DELETE' }
      )
      
      if (response.ok) {
        setConversations(prev => prev.filter(c => c.id !== conversationId))
      } else {
        throw new Error('Failed to delete conversation')
      }
    } catch (err: any) {
      alert(err.message || 'Failed to delete conversation')
    } finally {
      setDeletingId(null)
    }
  }

  const getModeLabel = (mode: string) => {
    switch (mode) {
      case 'all': return 'All Reports'
      case 'single': return 'Single Report'
      case 'minister': return 'Digital Minister'
      default: return mode
    }
  }

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'all': return 'bg-blue-500/10 text-blue-500'
      case 'single': return 'bg-green-500/10 text-green-500'
      case 'minister': return 'bg-purple-500/10 text-purple-500'
      default: return 'bg-gray-500/10 text-gray-500'
    }
  }

  const filteredConversations = conversations.filter(conv => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      (conv.title?.toLowerCase().includes(searchLower)) ||
      (conv.reports?.title?.toLowerCase().includes(searchLower))
    )
  })

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    
    return date.toLocaleDateString()
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Conversation History</h1>
          <p className="text-muted-foreground mt-1">
            Review and continue past conversations
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchConversations} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => router.push('/chat')}>
            <MessageSquare className="h-4 w-4 mr-2" />
            New Chat
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search conversations..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <Card className="border-destructive">
          <CardContent className="py-6 text-center">
            <p className="text-destructive mb-4">{error}</p>
            <Button variant="outline" onClick={fetchConversations}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Conversations List */}
      {!loading && !error && (
        <div className="space-y-3">
          {filteredConversations.length > 0 ? (
            filteredConversations.map((conv) => (
              <Card 
                key={conv.id}
                className="cursor-pointer hover:bg-accent/50 transition-colors"
                onClick={() => router.push(`/chat?conversation=${conv.id}`)}
              >
                <CardContent className="py-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold truncate">
                          {conv.title || 'Untitled Conversation'}
                        </h3>
                        <span className={`px-2 py-0.5 rounded text-xs ${getModeColor(conv.mode)}`}>
                          {getModeLabel(conv.mode)}
                        </span>
                      </div>
                      {conv.reports?.title && (
                        <div className="flex items-center gap-1 text-sm text-muted-foreground mb-1">
                          <FileText className="h-3 w-3" />
                          <span className="truncate">{conv.reports.title}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <MessageSquare className="h-3 w-3" />
                          {conv.message_count} messages
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(conv.updated_at || conv.created_at)}
                        </span>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="icon"
                      className="flex-shrink-0"
                      disabled={deletingId === conv.id}
                      onClick={(e) => handleDelete(conv.id, e)}
                    >
                      {deletingId === conv.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <History className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="font-semibold mb-2">No Conversations Yet</h3>
                <p className="text-sm text-muted-foreground max-w-sm mx-auto mb-4">
                  Start a new chat to begin building your conversation history.
                  Your conversations will be saved automatically.
                </p>
                <Button onClick={() => router.push('/chat')}>
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Start Chatting
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
