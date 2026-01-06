'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Search, FileText, Loader2, X, Filter } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface Report {
  id: string
  title: string
  source: string
  year: number | null
  category: string | null
  page_count: number | null
  has_summary: boolean
  created_at: string
}

interface ReportsResponse {
  items: Report[]
  total: number
  page: number
  limit: number
  has_more: boolean
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Known sources for filtering
const SOURCES = [
  'BCG', 'McKinsey', 'Deloitte', 'Accenture', 'KPMG', 'EY', 'PwC',
  'Capgemini', 'Google', 'Microsoft', 'DCAI', 'DFF', 'UAE Government',
  'World Economic Forum', 'OECD', 'Gartner', 'Forrester', 'IDC'
]

// Generate years from 2018 to current
const YEARS = Array.from({ length: new Date().getFullYear() - 2017 }, (_, i) => 2018 + i).reverse()

export default function LibraryPage() {
  const router = useRouter()
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [selectedSource, setSelectedSource] = useState<string | null>(null)
  const [selectedYear, setSelectedYear] = useState<number | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(false)
  const limit = 20

  const fetchReports = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      })
      if (search) params.set('search', search)
      if (selectedSource) params.set('source', selectedSource)
      if (selectedYear) params.set('year', selectedYear.toString())
      
      const res = await fetch(`${API_URL}/test/reports?${params}`)
      if (!res.ok) throw new Error('Failed to fetch reports')
      
      const data: ReportsResponse = await res.json()
      setReports(data.items || [])
      setTotal(data.total || 0)
      setHasMore(data.has_more || false)
    } catch (err: any) {
      setError(err.message || 'Failed to load reports')
      setReports([])
      setTotal(0)
      setHasMore(false)
    } finally {
      setLoading(false)
    }
  }, [page, search, selectedSource, selectedYear])

  useEffect(() => {
    fetchReports()
  }, [fetchReports])

  const clearFilters = () => {
    setSelectedSource(null)
    setSelectedYear(null)
    setSearch('')
    setPage(1)
  }

  const hasActiveFilters = selectedSource || selectedYear || search

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
  }

  const truncateTitle = (title: string, maxLen: number = 120) => {
    if (title.length <= maxLen) return title
    return title.substring(0, maxLen) + '...'
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Report Library</h1>
          <p className="text-muted-foreground mt-1">
            {total} strategic reports available
          </p>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="space-y-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search reports by title or content..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button type="submit">Search</Button>
        </form>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Filters:</span>
          </div>

          <Select
            value={selectedSource || "all"}
            onValueChange={(value) => {
              setSelectedSource(value === "all" ? null : value)
              setPage(1)
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Sources" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sources</SelectItem>
              {SOURCES.map((source) => (
                <SelectItem key={source} value={source}>
                  {source}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={selectedYear?.toString() || "all"}
            onValueChange={(value) => {
              setSelectedYear(value === "all" ? null : parseInt(value))
              setPage(1)
            }}
          >
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="All Years" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Years</SelectItem>
              {YEARS.map((year) => (
                <SelectItem key={year} value={year.toString()}>
                  {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              className="text-muted-foreground"
            >
              <X className="h-4 w-4 mr-1" />
              Clear filters
            </Button>
          )}
        </div>

        {/* Active Filter Badges */}
        {hasActiveFilters && (
          <div className="flex flex-wrap gap-2">
            {search && (
              <Badge variant="secondary" className="gap-1">
                Search: "{search}"
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => {
                    setSearch('')
                    setPage(1)
                  }}
                />
              </Badge>
            )}
            {selectedSource && (
              <Badge variant="secondary" className="gap-1">
                Source: {selectedSource}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => {
                    setSelectedSource(null)
                    setPage(1)
                  }}
                />
              </Badge>
            )}
            {selectedYear && (
              <Badge variant="secondary" className="gap-1">
                Year: {selectedYear}
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => {
                    setSelectedYear(null)
                    setPage(1)
                  }}
                />
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 text-red-500 bg-red-500/10 rounded-md">
          {error}
        </div>
      )}

      {/* Reports Grid */}
      {!loading && !error && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {reports.map((report) => (
              <Card 
                key={report.id} 
                className="hover:bg-accent/50 transition-colors cursor-pointer"
                onClick={() => router.push(`/library/${report.id}`)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start gap-3">
                    <FileText className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                    <CardTitle className="text-sm font-medium leading-tight">
                      {truncateTitle(report.title)}
                    </CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                    {report.source && report.source !== 'Unknown' && (
                      <span className="px-2 py-0.5 bg-primary/10 rounded">
                        {report.source}
                      </span>
                    )}
                    {report.year && (
                      <span className="px-2 py-0.5 bg-secondary rounded">
                        {report.year}
                      </span>
                    )}
                    {report.page_count && (
                      <span>{report.page_count} pages</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Empty State */}
          {reports.length === 0 && (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No reports found</h3>
              <p className="text-muted-foreground">
                {search ? 'Try adjusting your search query' : 'No reports have been uploaded yet'}
              </p>
            </div>
          )}

          {/* Pagination */}
          {reports.length > 0 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Showing {(page - 1) * limit + 1} - {Math.min(page * limit, total)} of {total}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!hasMore}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
