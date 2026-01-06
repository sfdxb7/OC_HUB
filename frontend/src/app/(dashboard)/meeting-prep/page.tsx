'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { 
  Calendar, 
  Users, 
  Target, 
  FileText,
  Sparkles,
  Clock,
  Loader2,
  Copy,
  Check,
  RefreshCw
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface BriefingResult {
  briefing: string
  sources: string[]
  model: string
  tokens_used: number
}

export default function MeetingPrepPage() {
  const [meetingTitle, setMeetingTitle] = useState('')
  const [participants, setParticipants] = useState('')
  const [purpose, setPurpose] = useState('')
  const [angle, setAngle] = useState<string>('balanced')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BriefingResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const angles = [
    { id: 'balanced', label: 'Balanced Overview' },
    { id: 'bold', label: 'Bold Vision' },
    { id: 'risk', label: 'Risk-Focused' },
    { id: 'data', label: 'Data-Heavy' },
  ]

  const handleGenerate = async () => {
    if (!meetingTitle.trim() || !participants.trim() || !purpose.trim()) {
      setError('Please fill in all required fields')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/test/meeting-prep`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: meetingTitle,
          participants,
          purpose,
          angle,
        }),
      })

      const data = await response.json()

      if (data.error) {
        throw new Error(data.error)
      }

      setResult(data)
    } catch (err: any) {
      console.error('Error generating briefing:', err)
      setError(err.message || 'Failed to generate briefing')
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = async () => {
    if (result?.briefing) {
      await navigator.clipboard.writeText(result.briefing)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleReset = () => {
    setMeetingTitle('')
    setParticipants('')
    setPurpose('')
    setAngle('balanced')
    setResult(null)
    setError(null)
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Meeting Prep</h1>
        <p className="text-muted-foreground mt-1">
          Generate AI-powered briefings for your meetings and interviews
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Meeting Details
            </CardTitle>
            <CardDescription>
              Provide context about your upcoming meeting
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Meeting Title / Topic <span className="text-destructive">*</span>
              </label>
              <Input
                placeholder="e.g., AI Governance Strategy Discussion"
                value={meetingTitle}
                onChange={(e) => setMeetingTitle(e.target.value)}
                disabled={loading}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Participants / Audience <span className="text-destructive">*</span>
              </label>
              <Input
                placeholder="e.g., Cabinet members, Tech CEOs, Media"
                value={participants}
                onChange={(e) => setParticipants(e.target.value)}
                disabled={loading}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Purpose / Goal <span className="text-destructive">*</span>
              </label>
              <textarea
                className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="What do you want to achieve? What's the context?"
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Briefing Angle</label>
              <div className="grid grid-cols-2 gap-2">
                {angles.map((a) => (
                  <Button 
                    key={a.id} 
                    variant={angle === a.id ? 'default' : 'outline'} 
                    className="justify-start"
                    onClick={() => setAngle(a.id)}
                    disabled={loading}
                  >
                    {a.label}
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
                disabled={loading || !meetingTitle.trim() || !participants.trim() || !purpose.trim()}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate Briefing
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
                  <FileText className="h-5 w-5" />
                  Generated Briefing
                </CardTitle>
                <CardDescription>
                  Your 2-minute briefing will appear here
                </CardDescription>
              </div>
              {result && (
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
              )}
            </div>
          </CardHeader>
          <CardContent className="flex-1">
            {loading && (
              <div className="flex flex-col items-center justify-center h-full py-12">
                <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
                <p className="text-sm text-muted-foreground">
                  Analyzing reports and generating briefing...
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  This may take 15-30 seconds
                </p>
              </div>
            )}

            {!loading && !result && (
              <>
                <div className="border-2 border-dashed border-muted rounded-lg p-8 text-center">
                  <Clock className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="font-semibold mb-2">Briefing Preview</h3>
                  <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                    Fill in the meeting details and click generate to create 
                    a concise briefing with key talking points, relevant statistics, 
                    and potential questions.
                  </p>
                </div>

                <div className="mt-6 space-y-3">
                  <h4 className="font-medium text-sm">Briefing will include:</h4>
                  <div className="grid grid-cols-1 gap-2 text-sm">
                    {[
                      { icon: Target, text: 'Key talking points tailored to your audience' },
                      { icon: FileText, text: 'Relevant statistics from strategic reports' },
                      { icon: Users, text: 'Anticipated questions and suggested responses' },
                      { icon: Sparkles, text: 'Strategic recommendation' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center gap-2 text-muted-foreground">
                        <item.icon className="h-4 w-4" />
                        <span>{item.text}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {result && (
              <div className="space-y-4">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {result.briefing}
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
                  Generated using {result.model} | {result.tokens_used} tokens
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
