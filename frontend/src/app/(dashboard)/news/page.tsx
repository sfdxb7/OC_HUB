'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { 
  Newspaper, 
  Link as LinkIcon, 
  Sparkles, 
  AlertTriangle,
  TrendingUp,
  Lightbulb,
  Target,
  MessageSquare,
  Loader2,
  Copy,
  Check,
  RefreshCw,
  ExternalLink
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface AnalysisResult {
  url: string
  title: string | null
  analysis: string
  model: string
}

export default function NewsAnalysisPage() {
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [showContentInput, setShowContentInput] = useState(false)

  const handleAnalyze = async () => {
    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    if (!content.trim()) {
      setError('Please paste the article content (Firecrawl integration coming soon)')
      setShowContentInput(true)
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/test/news-analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url,
          title: title || null,
          content,
        }),
      })

      const data = await response.json()

      if (data.error) {
        throw new Error(data.error)
      }

      setResult(data)
    } catch (err: any) {
      console.error('Error analyzing news:', err)
      setError(err.message || 'Failed to analyze article')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    if (result?.analysis) {
      await navigator.clipboard.writeText(result.analysis)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleReset = () => {
    setUrl('')
    setTitle('')
    setContent('')
    setResult(null)
    setError(null)
    setShowContentInput(false)
  }

  const analysisFramework = [
    {
      icon: Target,
      title: 'SO WHAT?',
      description: 'Why this matters for AI leadership and strategy',
      color: 'bg-blue-500/10 text-blue-500'
    },
    {
      icon: TrendingUp,
      title: 'UAE IMPLICATIONS',
      description: 'Specific impacts and opportunities for UAE',
      color: 'bg-green-500/10 text-green-500'
    },
    {
      icon: Lightbulb,
      title: 'OPPORTUNITIES',
      description: 'Actions UAE could take based on this news',
      color: 'bg-yellow-500/10 text-yellow-500'
    },
    {
      icon: AlertTriangle,
      title: 'RISKS',
      description: 'Potential challenges or threats to monitor',
      color: 'bg-red-500/10 text-red-500'
    },
    {
      icon: MessageSquare,
      title: 'TALKING POINT',
      description: 'Ministerial-grade response or position',
      color: 'bg-purple-500/10 text-purple-500'
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">News Analysis</h1>
        <p className="text-muted-foreground mt-1">
          Get "So What?" strategic analysis on AI news for UAE context
        </p>
      </div>

      {/* URL Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LinkIcon className="h-5 w-5" />
            Analyze News Article
          </CardTitle>
          <CardDescription>
            Paste a news article URL and content to get strategic implications for UAE AI leadership
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="https://example.com/article-about-ai..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1"
              disabled={loading}
            />
            {result ? (
              <Button variant="outline" onClick={handleReset}>
                <RefreshCw className="h-4 w-4 mr-2" />
                New
              </Button>
            ) : (
              <Button onClick={handleAnalyze} disabled={loading || !url.trim()}>
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Analyze
                  </>
                )}
              </Button>
            )}
          </div>

          {(showContentInput || content) && !result && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Article Title (optional)</label>
                <Input
                  placeholder="e.g., OpenAI Announces New Model..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={loading}
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Article Content <span className="text-destructive">*</span>
                </label>
                <textarea
                  className="w-full min-h-[200px] rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Paste the article content here... (automatic scraping coming soon with Firecrawl)"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  disabled={loading}
                />
                <p className="text-xs text-muted-foreground">
                  Note: Automatic article scraping via Firecrawl is coming soon. For now, please paste the article content.
                </p>
              </div>
            </>
          )}

          {error && (
            <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center">
              <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
              <p className="text-sm text-muted-foreground">
                Analyzing article through UAE AI leadership lens...
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                This may take 15-30 seconds
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analysis Result */}
      {result && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Analysis Results</CardTitle>
                <CardDescription className="flex items-center gap-2 mt-1">
                  {result.title || result.url}
                  <a 
                    href={result.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-primary hover:underline inline-flex items-center gap-1"
                  >
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={handleCopy}>
                {copied ? (
                  <>
                    <Check className="h-4 w-4 mr-2" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-2" />
                    Copy
                  </>
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {result.analysis}
              </ReactMarkdown>
            </div>
            <div className="pt-4 mt-4 border-t text-xs text-muted-foreground">
              Generated using {result.model}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analysis Framework (show when no result) */}
      {!loading && !result && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis Framework</CardTitle>
            <CardDescription>
              Every article will be analyzed through these lenses
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {analysisFramework.map((item) => (
                <Card key={item.title} className="bg-accent/30">
                  <CardContent className="pt-4">
                    <div className={`h-10 w-10 rounded-lg ${item.color} flex items-center justify-center mb-3`}>
                      <item.icon className="h-5 w-5" />
                    </div>
                    <h3 className="font-semibold text-sm">{item.title}</h3>
                    <p className="text-xs text-muted-foreground mt-1">{item.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
