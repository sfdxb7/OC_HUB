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
  ArrowRight
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Stats {
  total_reports: number
  total_conversations: number
  total_databank_items: number
}

export default function DashboardPage() {
  const router = useRouter()
  const [stats, setStats] = useState<Stats>({ total_reports: 0, total_conversations: 0, total_databank_items: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_URL}/test/supabase`)
      .then(res => res.json())
      .then(data => {
        if (data.stats) {
          setStats(data.stats)
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const statCards = [
    { 
      title: 'Total Reports', 
      value: stats.total_reports || 20, // Fallback for demo
      icon: FileText, 
      color: 'text-blue-500',
      href: '/library'
    },
    { 
      title: 'Conversations', 
      value: stats.total_conversations, 
      icon: MessageSquare, 
      color: 'text-green-500',
      href: '/history'
    },
    { 
      title: 'Data Bank Items', 
      value: stats.total_databank_items, 
      icon: Database, 
      color: 'text-purple-500',
      href: '/databank'
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
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Welcome to DCAI Intelligence Hub
        </p>
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
              <stat.icon className={`h-5 w-5 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stat.value}</div>
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

      {/* Recent Insights Placeholder */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Latest Insights</h2>
        <Card>
          <CardContent className="py-8 text-center">
            <Lightbulb className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="font-semibold mb-2">Aha Moments Coming Soon</h3>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              This section will display contrarian insights and surprising findings 
              extracted from your strategic reports.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
