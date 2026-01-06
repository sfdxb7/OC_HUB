'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { 
  FileText, 
  MessageSquare, 
  Database, 
  Lightbulb,
  TrendingUp,
  Clock,
  ArrowRight,
  Sparkles,
  BarChart3,
  RefreshCw
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Stats {
  total_reports: number
  total_conversations: number
  total_databank_items: number
}

interface AhaMoment {
  id: string
  content: string
  source: string
  report_title?: string
  reports?: {
    title: string
    source: string
  }
}

interface TopSource {
  name: string
  count: number
}

export default function DashboardPage() {
  const router = useRouter()
  const [stats, setStats] = useState<Stats>({ total_reports: 0, total_conversations: 0, total_databank_items: 0 })
  const [ahaMoments, setAhaMoments] = useState<AhaMoment[]>([])
  const [topSources, setTopSources] = useState<TopSource[]>([])
  const [loading, setLoading] = useState(true)
  const [insightsLoading, setInsightsLoading] = useState(true)

  // Fetch stats
  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/test/reports?limit=1`).then(res => res.json()),
      fetch(`${API_URL}/test/databank?type=aha_moment&limit=5`).then(res => res.json()),
      fetch(`${API_URL}/test/sources`).then(res => res.json()),
    ])
      .then(([reportsData, databankData, sourcesData]) => {
        // Set stats from reports
        setStats({
          total_reports: reportsData.total || 0,
          total_conversations: 0, // Will be updated when we have auth
          total_databank_items: databankData.total || 0
        })
        
        // Set aha moments
        if (databankData.items) {
          setAhaMoments(databankData.items.map((item: any) => ({
            id: item.id,
            content: item.content,
            source: item.reports?.source || 'Unknown',
            report_title: item.reports?.title || 'Unknown Report'
          })))
        }
        
        // Set top sources
        if (sourcesData.sources) {
          const sourceCounts: Record<string, number> = {}
          sourcesData.sources.forEach((s: string) => {
            sourceCounts[s] = (sourceCounts[s] || 0) + 1
          })
          const sorted = Object.entries(sourceCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([name, count]) => ({ name, count }))
          setTopSources(sorted)
        }
      })
      .catch(console.error)
      .finally(() => {
        setLoading(false)
        setInsightsLoading(false)
      })
  }, [])

  const statCards = [
    { 
      title: 'Total Reports', 
      value: stats.total_reports,
      icon: FileText, 
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      href: '/library'
    },
    { 
      title: 'Data Bank Items', 
      value: stats.total_databank_items, 
      icon: Database, 
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
      href: '/databank'
    },
    { 
      title: 'Top Source', 
      value: topSources[0]?.name || 'Loading...', 
      subtitle: topSources[0] ? `${topSources[0].count} reports` : '',
      icon: BarChart3, 
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      href: '/library'
    },
  ]

  const quickActions = [
    { 
      title: 'Start New Chat', 
      description: 'Ask questions about all reports',
      icon: MessageSquare,
      href: '/chat',
      color: 'bg-blue-500/10 text-blue-500'
    },
    { 
      title: 'Meeting Prep', 
      description: 'Generate a briefing for your next meeting',
      icon: Clock,
      href: '/meeting-prep',
      color: 'bg-green-500/10 text-green-500'
    },
    { 
      title: 'Browse Library', 
      description: 'Explore strategic reports',
      icon: FileText,
      href: '/library',
      color: 'bg-purple-500/10 text-purple-500'
    },
    { 
      title: 'Analyze News', 
      description: 'Get "So What?" analysis on news',
      icon: TrendingUp,
      href: '/news',
      color: 'bg-orange-500/10 text-orange-500'
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Welcome to DCAI Intelligence Hub
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => window.location.reload()}
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {statCards.map((stat) => (
          <Card 
            key={stat.title} 
            className="cursor-pointer hover:bg-accent/50 transition-colors"
            onClick={() => router.push(stat.href)}
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-8 w-20" />
              ) : (
                <>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  {stat.subtitle && (
                    <p className="text-xs text-muted-foreground mt-1">{stat.subtitle}</p>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <Card 
              key={action.title}
              className="cursor-pointer hover:bg-accent/50 transition-colors group"
              onClick={() => router.push(action.href)}
            >
              <CardContent className="pt-6">
                <div className={`h-12 w-12 rounded-lg ${action.color} flex items-center justify-center mb-4`}>
                  <action.icon className="h-6 w-6" />
                </div>
                <h3 className="font-semibold mb-1 flex items-center gap-2">
                  {action.title}
                  <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </h3>
                <p className="text-sm text-muted-foreground">{action.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Aha Moments / Insights */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-yellow-500" />
            <h2 className="text-xl font-semibold">Latest Aha Moments</h2>
          </div>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => router.push('/databank?type=aha_moment')}
          >
            View All
            <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
        
        {insightsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardContent className="pt-4">
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-3/4" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : ahaMoments.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {ahaMoments.map((moment) => (
              <Card 
                key={moment.id}
                className="hover:bg-accent/30 transition-colors"
              >
                <CardContent className="pt-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-yellow-500/10 shrink-0">
                      <Lightbulb className="h-4 w-4 text-yellow-500" />
                    </div>
                    <div className="space-y-2">
                      <p className="text-sm leading-relaxed">{moment.content}</p>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-xs">
                          {moment.source}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-8 text-center">
              <Lightbulb className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="font-semibold mb-2">No Aha Moments Yet</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Insights will appear here as reports are processed and analyzed.
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Source Distribution */}
      {topSources.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Report Sources</h2>
          <Card>
            <CardContent className="pt-4">
              <div className="space-y-3">
                {topSources.map((source, index) => (
                  <div key={source.name} className="flex items-center gap-3">
                    <span className="text-sm font-medium w-24 truncate">{source.name}</span>
                    <div className="flex-1 bg-muted rounded-full h-2 overflow-hidden">
                      <div 
                        className="h-full bg-primary rounded-full transition-all"
                        style={{ 
                          width: `${(source.count / topSources[0].count) * 100}%` 
                        }}
                      />
                    </div>
                    <span className="text-sm text-muted-foreground w-12 text-right">
                      {source.count}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
