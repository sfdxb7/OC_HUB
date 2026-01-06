'use client'

import { useState, useEffect } from 'react'
import { 
  Database, 
  BarChart3, 
  Quote, 
  Lightbulb, 
  ListChecks,
  Search,
  Loader2,
  RefreshCw,
  Copy,
  Check,
  FileText,
  ExternalLink
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type DataType = 'all' | 'statistic' | 'quote' | 'finding' | 'aha_moment'

interface DataBankItem {
  id: string
  report_id: string
  type: string
  content: string
  context: string | null
  source_page: number | null
  tags: string[] | null
  created_at: string
  report?: { title: string } | null
}

const dataTypes = [
  { id: 'all', label: 'All', icon: Database, color: 'text-gray-500' },
  { id: 'statistic', label: 'Statistics', icon: BarChart3, color: 'text-blue-500' },
  { id: 'quote', label: 'Quotes', icon: Quote, color: 'text-purple-500' },
  { id: 'finding', label: 'Key Findings', icon: ListChecks, color: 'text-green-500' },
  { id: 'aha_moment', label: 'Aha Moments', icon: Lightbulb, color: 'text-yellow-500' },
] as const

export default function DataBankPage() {
  const [activeType, setActiveType] = useState<DataType>('all')
  const [search, setSearch] = useState('')
  const [items, setItems] = useState<DataBankItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const fetchDataBank = async () => {
    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      if (activeType !== 'all') {
        params.append('type', activeType)
      }
      if (search) {
        params.append('search', search)
      }
      params.append('limit', '100')

      const response = await fetch(`${API_URL}/test/databank?${params.toString()}`)
      const data = await response.json()

      if (data.error) {
        throw new Error(data.error)
      }

      setItems(data.items || [])
      setTotal(data.total || 0)
    } catch (err: any) {
      console.error('Error fetching data bank:', err)
      setError(err.message || 'Failed to load data bank')
      setItems([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDataBank()
  }, [activeType])

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchDataBank()
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  const handleCopy = async (item: DataBankItem) => {
    await navigator.clipboard.writeText(item.content)
    setCopiedId(item.id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'statistic': return BarChart3
      case 'quote': return Quote
      case 'finding': return ListChecks
      case 'aha_moment': return Lightbulb
      default: return Database
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'statistic': return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
      case 'quote': return 'bg-purple-500/10 text-purple-500 border-purple-500/20'
      case 'finding': return 'bg-green-500/10 text-green-500 border-green-500/20'
      case 'aha_moment': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
      default: return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'statistic': return 'Statistic'
      case 'quote': return 'Quote'
      case 'finding': return 'Finding'
      case 'aha_moment': return 'Aha Moment'
      default: return type
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Bank</h1>
          <p className="text-muted-foreground mt-1">
            Browse extracted statistics, quotes, findings, and insights from all reports
          </p>
        </div>
        <Button variant="outline" onClick={fetchDataBank} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search data bank..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {dataTypes.map((type) => (
            <Button
              key={type.id}
              variant={activeType === type.id ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveType(type.id as DataType)}
            >
              <type.icon className={`h-4 w-4 mr-2 ${activeType === type.id ? '' : type.color}`} />
              {type.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Stats */}
      {!loading && (
        <div className="text-sm text-muted-foreground">
          Showing {items.length} of {total} items
        </div>
      )}

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
            <Button variant="outline" onClick={fetchDataBank}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!loading && !error && items.length === 0 && (
        <Card>
          <CardContent className="py-16 text-center">
            <Database className="h-16 w-16 mx-auto text-muted-foreground mb-6" />
            <h2 className="text-xl font-semibold mb-2">No Data Found</h2>
            <p className="text-muted-foreground max-w-lg mx-auto mb-6">
              {search ? (
                `No items matching "${search}" found in the data bank.`
              ) : (
                <>
                  The data bank is currently empty. Data will be populated when reports are 
                  processed with the enrichment pipeline to extract statistics, quotes, findings, 
                  and insights.
                </>
              )}
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto text-left">
              <Card className="bg-blue-500/10 border-blue-500/20">
                <CardContent className="pt-4">
                  <BarChart3 className="h-8 w-8 text-blue-500 mb-2" />
                  <h3 className="font-medium">Statistics</h3>
                  <p className="text-sm text-muted-foreground">Key numbers and metrics</p>
                </CardContent>
              </Card>
              <Card className="bg-purple-500/10 border-purple-500/20">
                <CardContent className="pt-4">
                  <Quote className="h-8 w-8 text-purple-500 mb-2" />
                  <h3 className="font-medium">Quotes</h3>
                  <p className="text-sm text-muted-foreground">Quotable language</p>
                </CardContent>
              </Card>
              <Card className="bg-green-500/10 border-green-500/20">
                <CardContent className="pt-4">
                  <ListChecks className="h-8 w-8 text-green-500 mb-2" />
                  <h3 className="font-medium">Findings</h3>
                  <p className="text-sm text-muted-foreground">Key conclusions</p>
                </CardContent>
              </Card>
              <Card className="bg-yellow-500/10 border-yellow-500/20">
                <CardContent className="pt-4">
                  <Lightbulb className="h-8 w-8 text-yellow-500 mb-2" />
                  <h3 className="font-medium">Aha Moments</h3>
                  <p className="text-sm text-muted-foreground">Surprising insights</p>
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Items */}
      {!loading && !error && items.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => {
            const TypeIcon = getTypeIcon(item.type)
            return (
              <Card key={item.id} className={`${getTypeColor(item.type)} hover:shadow-lg transition-shadow`}>
                <CardContent className="pt-4 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <TypeIcon className="h-4 w-4" />
                      <span className="text-xs font-medium uppercase">
                        {getTypeLabel(item.type)}
                      </span>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-6 w-6"
                      onClick={() => handleCopy(item)}
                    >
                      {copiedId === item.id ? (
                        <Check className="h-3 w-3" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </Button>
                  </div>
                  
                  <p className="text-sm line-clamp-4">
                    {item.type === 'quote' ? `"${item.content}"` : item.content}
                  </p>
                  
                  {item.context && (
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {item.context}
                    </p>
                  )}
                  
                  <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
                    {item.report?.title ? (
                      <a 
                        href={`/library/${item.report_id}`}
                        className="flex items-center gap-1 hover:text-foreground truncate max-w-[80%]"
                      >
                        <FileText className="h-3 w-3 flex-shrink-0" />
                        <span className="truncate">{item.report.title}</span>
                      </a>
                    ) : (
                      <span className="truncate">Unknown source</span>
                    )}
                    {item.source_page && (
                      <span>p.{item.source_page}</span>
                    )}
                  </div>
                  
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {item.tags.slice(0, 3).map((tag, i) => (
                        <span 
                          key={i}
                          className="px-1.5 py-0.5 rounded text-[10px] bg-background/50"
                        >
                          {tag}
                        </span>
                      ))}
                      {item.tags.length > 3 && (
                        <span className="text-[10px]">+{item.tags.length - 3} more</span>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
