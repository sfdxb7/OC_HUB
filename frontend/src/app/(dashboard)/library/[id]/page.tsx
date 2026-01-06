'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { 
  ChevronRight, FileText, Loader2, BookOpen, BarChart3, 
  Quote, Lightbulb, ListChecks, MessageSquare, AlertCircle 
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

interface KeyFinding {
  finding: string
  evidence?: string
  page?: number
  significance?: string
}

interface Statistic {
  stat: string
  context?: string
  source_page?: number
}

interface QuoteItem {
  quote: string
  speaker?: string
  context?: string
  page?: number
}

interface AhaMoment {
  insight: string
  why_contrarian?: string
  implications?: string
}

interface Recommendation {
  recommendation: string
  rationale?: string
  page?: number
  priority?: string
}

interface ReportDetail {
  id: string
  title: string
  source: string
  year: number | null
  category: string | null
  page_count: number | null
  executive_summary: string | null
  key_findings: KeyFinding[]
  statistics: Statistic[]
  quotes: QuoteItem[]
  aha_moments: AhaMoment[]
  recommendations: Recommendation[]
  methodology: string | null
  limitations: string | null
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ReportDetailPage() {
  const router = useRouter()
  const params = useParams()
  const [report, setReport] = useState<ReportDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'summary' | 'findings' | 'stats' | 'quotes' | 'insights' | 'recommendations'>('summary')

  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API_URL}/test/reports/${params.id}`)
        if (!res.ok) throw new Error('Failed to fetch report')
        const data = await res.json()
        if (data.error) throw new Error(data.error)
        setReport(data)
      } catch (err: any) {
        setError(err.message || 'Failed to load report')
      } finally {
        setLoading(false)
      }
    }
    if (params.id) fetchReport()
  }, [params.id])

  const tabs = [
    { id: 'summary', label: 'Summary', icon: BookOpen, count: undefined },
    { id: 'findings', label: 'Key Findings', icon: ListChecks, count: report?.key_findings?.length },
    { id: 'stats', label: 'Statistics', icon: BarChart3, count: report?.statistics?.length },
    { id: 'quotes', label: 'Quotes', icon: Quote, count: report?.quotes?.length },
    { id: 'insights', label: 'Aha Moments', icon: Lightbulb, count: report?.aha_moments?.length },
    { id: 'recommendations', label: 'Recommendations', icon: ListChecks, count: report?.recommendations?.length },
  ] as const

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertCircle className="h-12 w-12 text-red-500" />
        <p className="text-lg">{error || 'Report not found'}</p>
        <Button onClick={() => router.push('/library')}>Back to Library</Button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b">
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
          <Button variant="ghost" size="sm" onClick={() => router.push('/library')}>
            <ChevronRight className="h-4 w-4 rotate-180 mr-1" />
            Library
          </Button>
          <span>/</span>
          <span className="truncate max-w-xs">{report.title.substring(0, 50)}...</span>
        </div>
        
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4 flex-1">
            <FileText className="h-8 w-8 text-primary flex-shrink-0 mt-1" />
            <div className="min-w-0">
              <h1 className="text-xl font-semibold leading-tight mb-2">{report.title}</h1>
              <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
                {report.source && report.source !== 'Unknown' && (
                  <span className="px-2 py-0.5 bg-primary/10 rounded">{report.source}</span>
                )}
                {report.year && <span className="px-2 py-0.5 bg-secondary rounded">{report.year}</span>}
                {report.page_count && <span>{report.page_count} pages</span>}
              </div>
            </div>
          </div>
          <Button onClick={() => router.push(`/chat?document=${report.id}`)}>
            <MessageSquare className="h-4 w-4 mr-2" />
            Chat with Report
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b px-6">
        <div className="flex gap-1 overflow-x-auto py-2">
          {tabs.map((tab) => (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon className="h-4 w-4 mr-1" />
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span className="ml-1 text-xs bg-primary/20 px-1.5 py-0.5 rounded">{tab.count}</span>
              )}
            </Button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'summary' && (
          <Card>
            <CardHeader><CardTitle>Executive Summary</CardTitle></CardHeader>
            <CardContent>
              {report.executive_summary ? (
                <p className="text-muted-foreground whitespace-pre-wrap">{report.executive_summary}</p>
              ) : (
                <p className="text-muted-foreground text-center py-8">No executive summary available.</p>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === 'findings' && (
          <div className="space-y-4">
            {report.key_findings?.length > 0 ? (
              report.key_findings.map((f, i) => (
                <Card key={i}>
                  <CardContent className="pt-4">
                    <div className="flex gap-3">
                      <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-sm flex items-center justify-center font-medium">{i + 1}</span>
                      <div>
                        <p className="font-medium">{f.finding}</p>
                        {f.evidence && <p className="mt-2 text-sm text-muted-foreground"><strong>Evidence:</strong> {f.evidence}</p>}
                        {f.page && <p className="mt-1 text-xs text-muted-foreground">Page {f.page}</p>}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card><CardContent className="py-8 text-center text-muted-foreground">No key findings extracted.</CardContent></Card>
            )}
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.statistics?.length > 0 ? (
              report.statistics.map((s, i) => (
                <Card key={i}>
                  <CardContent className="pt-4">
                    <div className="flex gap-3">
                      <BarChart3 className="h-5 w-5 text-blue-500 flex-shrink-0" />
                      <div>
                        <p className="font-medium">{s.stat}</p>
                        {s.context && <p className="mt-1 text-sm text-muted-foreground">{s.context}</p>}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card className="col-span-full"><CardContent className="py-8 text-center text-muted-foreground">No statistics extracted.</CardContent></Card>
            )}
          </div>
        )}

        {activeTab === 'quotes' && (
          <div className="space-y-4">
            {report.quotes?.length > 0 ? (
              report.quotes.map((q, i) => (
                <Card key={i}>
                  <CardContent className="pt-4">
                    <blockquote className="border-l-4 border-primary/30 pl-4">
                      <p className="italic text-lg">"{q.quote}"</p>
                      {q.speaker && <footer className="mt-2 text-sm text-muted-foreground">- {q.speaker}</footer>}
                    </blockquote>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card><CardContent className="py-8 text-center text-muted-foreground">No quotes extracted.</CardContent></Card>
            )}
          </div>
        )}

        {activeTab === 'insights' && (
          <div className="space-y-4">
            {report.aha_moments?.length > 0 ? (
              report.aha_moments.map((a, i) => (
                <Card key={i} className="border-yellow-500/30">
                  <CardContent className="pt-4">
                    <div className="flex gap-3">
                      <Lightbulb className="h-5 w-5 text-yellow-500 flex-shrink-0" />
                      <div>
                        <p className="font-medium">{a.insight}</p>
                        {a.why_contrarian && <p className="mt-2 text-sm text-muted-foreground"><strong>Why surprising:</strong> {a.why_contrarian}</p>}
                        {a.implications && <p className="mt-1 text-sm text-muted-foreground"><strong>Implications:</strong> {a.implications}</p>}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card><CardContent className="py-8 text-center text-muted-foreground">No contrarian insights extracted.</CardContent></Card>
            )}
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            {report.recommendations?.length > 0 ? (
              report.recommendations.map((r, i) => (
                <Card key={i}>
                  <CardContent className="pt-4">
                    <div className="flex gap-3">
                      <span className="w-6 h-6 rounded-full bg-green-500/10 text-green-500 text-sm flex items-center justify-center font-medium">{i + 1}</span>
                      <div>
                        <p className="font-medium">{r.recommendation}</p>
                        {r.rationale && <p className="mt-2 text-sm text-muted-foreground"><strong>Rationale:</strong> {r.rationale}</p>}
                        {r.priority && (
                          <span className={`mt-2 inline-block px-2 py-0.5 rounded text-xs ${
                            r.priority.toLowerCase() === 'high' ? 'bg-red-500/10 text-red-500' :
                            r.priority.toLowerCase() === 'medium' ? 'bg-yellow-500/10 text-yellow-500' : 'bg-gray-500/10'
                          }`}>{r.priority} priority</span>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <Card><CardContent className="py-8 text-center text-muted-foreground">No recommendations extracted.</CardContent></Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
