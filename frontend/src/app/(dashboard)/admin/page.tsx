'use client'

import { useRouter } from 'next/navigation'
import { 
  Settings, 
  Upload, 
  Users, 
  Database,
  FileText,
  Activity,
  CheckCircle,
  AlertTriangle
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function AdminDashboardPage() {
  const router = useRouter()

  const adminCards = [
    {
      title: 'Bulk Upload',
      description: 'Upload ZIP files of MinerU-processed reports',
      icon: Upload,
      href: '/admin/upload',
      color: 'bg-blue-500/10 text-blue-500',
      stats: '405 reports'
    },
    {
      title: 'User Management',
      description: 'Manage user accounts and permissions',
      icon: Users,
      href: '/admin/users',
      color: 'bg-green-500/10 text-green-500',
      stats: '1 admin'
    },
    {
      title: 'RAGFlow Status',
      description: 'Check document processing and vector DB status',
      icon: Database,
      href: '#',
      color: 'bg-purple-500/10 text-purple-500',
      stats: '362 parsed'
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Manage the DCAI Intelligence Platform
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Backend</p>
                <p className="text-lg font-semibold">Online</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">RAGFlow</p>
                <p className="text-lg font-semibold">Connected</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Supabase</p>
                <p className="text-lg font-semibold">Connected</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">LLM Gateway</p>
                <p className="text-lg font-semibold">Active</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Admin Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {adminCards.map((card) => (
          <Card 
            key={card.title}
            className="cursor-pointer hover:bg-accent/50 transition-colors"
            onClick={() => router.push(card.href)}
          >
            <CardHeader>
              <div className={`h-12 w-12 rounded-lg ${card.color} flex items-center justify-center mb-2`}>
                <card.icon className="h-6 w-6" />
              </div>
              <CardTitle className="text-lg">{card.title}</CardTitle>
              <CardDescription>{card.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{card.stats}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Processing Queue Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Processing Queue
          </CardTitle>
          <CardDescription>
            Recent and ongoing processing jobs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed border-muted rounded-lg p-8 text-center">
            <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-4" />
            <h3 className="font-semibold mb-2">All Caught Up</h3>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              No processing jobs in queue. Upload new reports to start processing.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
