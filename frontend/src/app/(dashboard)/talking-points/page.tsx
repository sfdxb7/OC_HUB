'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { 
  ListChecks, 
  Mic, 
  Copy, 
  Download,
  Sparkles,
  Target,
  Loader2,
  Check,
  RefreshCw
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TalkingPointsResult {
  talking_points: string
  sources: string[]
  model: string
}

export default function TalkingPointsPage() {
  const [topic, setTopic] = useState('')
  const [audience, setAudience] = useState('')
  const [tone, setTone] = useState<string>('professional')
  const [numPoints, setNumPoints] = useState<number>(5)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TalkingPointsResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const tones = [
    { id: 'professional', label: 'Professional' },
    { id: 'visionary', label: 'Visionary' },
    { id: 'cautious', label: 'Cautious' },
    { id: 'bold', label: 'Bold' },
  ]

  const pointOptions = [3, 5, 7, 10]

  const handleGenerate = async () => {
    if (!topic.trim() || !audience.trim()) {
      setError('Please fill in topic and audience')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/test/talking-points`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic,
          audience,
          tone,
          num_points: numPoints,
        }),
      })

      const data = await response.json()

      if (data.error) {
        throw new Error(data.error)
      }

      setResult(data)
    } catch (err: any) {
      console.error('Error generating talking points:', err)
      setError(err.message || 'Failed to generate talking points')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    if (result?.talking_points) {
      await navigator.clipboard.writeText(result.talking_points)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDownload = () => {
    if (result?.talking_points) {
      const blob = new Blob([result.talking_points], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `talking-points-${topic.toLowerCase().replace(/\s+/g, '-')}.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  const handleReset = () => {
    setTopic('')
    setAudience('')
    setTone('professional')
    setNumPoints(5)
    setResult(null)
    setError(null)
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Talking Points Generator</h1>
        <p className="text-muted-foreground mt-1">
          Generate structured talking points for any AI-related topic
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Topic Configuration
            </CardTitle>
            <CardDescription>
              Define what you need talking points about
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Topic <span className="text-destructive">*</span>
              </label>
              <Input
                placeholder="e.g., UAE's AI Leadership, Responsible AI, Talent Strategy"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={loading}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Audience <span className="text-destructive">*</span>
              </label>
              <Input
                placeholder="e.g., World Government Summit, Tech Conference, Media Interview"
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
                disabled={loading}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Tone</label>
              <div className="grid grid-cols-2 gap-2">
                {tones.map((t) => (
                  <Button 
                    key={t.id} 
                    variant={tone === t.id ? 'default' : 'outline'}
                    onClick={() => setTone(t.id)}
                    disabled={loading}
                  >
                    {t.label}
                  </Button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Number of Points</label>
              <div className="flex gap-2">
                {pointOptions.map((n) => (
                  <Button 
                    key={n} 
                    variant={numPoints === n ? 'default' : 'outline'} 
                    size="sm"
                    onClick={() => setNumPoints(n)}
                    disabled={loading}
                  >
                    {n} points
                  </Button>
                ))}
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
                {error}
              </div>
            )}

            <div className="flex gap-2">
              <Button 
                className="flex-1" 
                onClick={handleGenerate}
                disabled={loading || !topic.trim() || !audience.trim()}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate Talking Points
                  </>
                )}
              </Button>
              {result && (
                <Button variant="outline" onClick={handleReset}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Output Preview */}
        <Card className="flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <ListChecks className="h-5 w-5" />
                  Generated Talking Points
                </CardTitle>
                <CardDescription>
                  Your talking points will appear here
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1">
            {loading && (
              <div className="flex flex-col items-center justify-center h-full py-12">
                <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
                <p className="text-sm text-muted-foreground">
                  Searching reports and generating talking points...
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  This may take 15-30 seconds
                </p>
              </div>
            )}

            {!loading && !result && (
              <>
                <div className="border-2 border-dashed border-muted rounded-lg p-8 text-center">
                  <Mic className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="font-semibold mb-2">Ready for Your Input</h3>
                  <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                    Enter a topic and configure options to generate 
                    structured talking points backed by data from strategic reports.
                  </p>
                </div>

                <div className="mt-6 flex gap-2">
                  <Button variant="outline" className="flex-1" disabled>
                    <Copy className="h-4 w-4 mr-2" />
                    Copy All
                  </Button>
                  <Button variant="outline" className="flex-1" disabled>
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>

                <div className="mt-6 space-y-3">
                  <h4 className="font-medium text-sm">Each point will include:</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>Main argument or position</li>
                    <li>Supporting statistic or evidence</li>
                    <li>Source reference for credibility</li>
                    <li>Why it matters</li>
                  </ul>
                </div>
              </>
            )}

            {result && (
              <div className="space-y-4">
                <div className="flex gap-2 mb-4">
                  <Button variant="outline" className="flex-1" onClick={handleCopy}>
                    {copied ? (
                      <>
                        <Check className="h-4 w-4 mr-2" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 mr-2" />
                        Copy All
                      </>
                    )}
                  </Button>
                  <Button variant="outline" className="flex-1" onClick={handleDownload}>
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>

                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {result.talking_points}
                  </ReactMarkdown>
                </div>
                
                {result.sources && result.sources.length > 0 && (
                  <div className="pt-4 border-t">
                    <h4 className="font-medium text-sm mb-2">Sources Used:</h4>
                    <div className="flex flex-wrap gap-2">
                      {result.sources.map((source, i) => (
                        <span 
                          key={i}
                          className="px-2 py-1 rounded bg-muted text-xs"
                        >
                          {source}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="pt-4 border-t text-xs text-muted-foreground">
                  Generated using {result.model}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
