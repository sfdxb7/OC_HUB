'use client'

import { useState, useRef, useEffect } from 'react'
import { 
  Upload, 
  FileArchive, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  FolderOpen,
  Play,
  RefreshCw,
  FileText
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ProcessingResult {
  total_found: number
  processing: number
  processed: number
  skipped: number
  failed: number
  details: Array<{
    folder: string
    status: string
    title?: string
    error?: string
  }>
}

interface ProcessingStatus {
  total_reports: number
  with_summary: number
  with_source: number
  with_findings: number
  missing_extraction: number
}

export default function BulkUploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Batch processing state
  const [processing, setProcessing] = useState(false)
  const [processLimit, setProcessLimit] = useState(10)
  const [processResult, setProcessResult] = useState<ProcessingResult | null>(null)
  const [processError, setProcessError] = useState<string | null>(null)
  const [status, setStatus] = useState<ProcessingStatus | null>(null)
  const [statusLoading, setStatusLoading] = useState(true)

  // Fetch status on load
  useEffect(() => {
    fetchStatus()
  }, [])

  const fetchStatus = async () => {
    setStatusLoading(true)
    try {
      const res = await fetch(`${API_URL}/test/process-status`)
      if (res.ok) {
        const data = await res.json()
        setStatus(data)
      }
    } catch (err) {
      console.error('Failed to fetch status:', err)
    } finally {
      setStatusLoading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.name.endsWith('.zip')) {
      setSelectedFile(file)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file && file.name.endsWith('.zip')) {
      setSelectedFile(file)
    }
  }

  const startBatchProcessing = async () => {
    setProcessing(true)
    setProcessResult(null)
    setProcessError(null)
    
    try {
      const res = await fetch(`${API_URL}/test/process-batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          limit: processLimit,
          max_concurrent: 3,
          force_reprocess: false
        })
      })
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      
      const data = await res.json()
      
      if (data.error) {
        setProcessError(data.error)
      } else {
        setProcessResult(data)
        fetchStatus() // Refresh status after processing
      }
    } catch (err: any) {
      setProcessError(err.message || 'Processing failed')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Report Processing</h1>
        <p className="text-muted-foreground mt-1">
          Process MinerU reports and extract intelligence
        </p>
      </div>

      {/* Status Overview */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Processing Status
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={fetchStatus} disabled={statusLoading}>
              <RefreshCw className={`h-4 w-4 ${statusLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {statusLoading && !status ? (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading status...
            </div>
          ) : status ? (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold">{status.total_reports}</div>
                <div className="text-xs text-muted-foreground">Total Reports</div>
              </div>
              <div className="text-center p-3 bg-green-500/10 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{status.with_summary}</div>
                <div className="text-xs text-muted-foreground">With Summary</div>
              </div>
              <div className="text-center p-3 bg-blue-500/10 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{status.with_source}</div>
                <div className="text-xs text-muted-foreground">With Source</div>
              </div>
              <div className="text-center p-3 bg-purple-500/10 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">{status.with_findings}</div>
                <div className="text-xs text-muted-foreground">With Findings</div>
              </div>
              <div className="text-center p-3 bg-yellow-500/10 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">{status.missing_extraction}</div>
                <div className="text-xs text-muted-foreground">Need Extraction</div>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground">Unable to load status</p>
          )}
        </CardContent>
      </Card>

      {/* Batch Processing */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Process Local Reports
          </CardTitle>
          <CardDescription>
            Process MinerU reports from the configured local folder
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-end gap-4">
            <div className="space-y-2">
              <Label htmlFor="limit">Reports to process</Label>
              <Input
                id="limit"
                type="number"
                min={1}
                max={405}
                value={processLimit}
                onChange={(e) => setProcessLimit(parseInt(e.target.value) || 10)}
                className="w-32"
                disabled={processing}
              />
            </div>
            <Button 
              onClick={startBatchProcessing}
              disabled={processing}
              className="min-w-[200px]"
            >
              {processing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Start Processing
                </>
              )}
            </Button>
          </div>

          <p className="text-xs text-muted-foreground">
            Path: C:\myprojects\REVIEW\NewHUB\processed_reports_mineru (405 reports available)
          </p>

          {/* Processing Error */}
          {processError && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-4 w-4" />
                <span className="font-medium">Error</span>
              </div>
              <p className="mt-1 text-sm">{processError}</p>
            </div>
          )}

          {/* Processing Results */}
          {processResult && (
            <div className="space-y-4">
              <div className="p-4 bg-muted rounded-lg">
                <div className="flex items-center gap-4 mb-4">
                  <Badge variant="outline" className="gap-1">
                    Found: {processResult.total_found}
                  </Badge>
                  <Badge variant="secondary" className="gap-1 bg-green-500/10 text-green-600">
                    <CheckCircle className="h-3 w-3" />
                    Processed: {processResult.processed}
                  </Badge>
                  <Badge variant="secondary" className="gap-1">
                    Skipped: {processResult.skipped}
                  </Badge>
                  {processResult.failed > 0 && (
                    <Badge variant="destructive" className="gap-1">
                      <AlertCircle className="h-3 w-3" />
                      Failed: {processResult.failed}
                    </Badge>
                  )}
                </div>

                {processResult.details && processResult.details.length > 0 && (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {processResult.details.map((item, i) => (
                      <div 
                        key={i} 
                        className={`text-sm p-2 rounded ${
                          item.status === 'processed' 
                            ? 'bg-green-500/10' 
                            : item.status === 'failed' 
                            ? 'bg-red-500/10' 
                            : 'bg-muted'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {item.status === 'processed' && <CheckCircle className="h-3 w-3 text-green-500" />}
                          {item.status === 'failed' && <AlertCircle className="h-3 w-3 text-red-500" />}
                          <span className="truncate flex-1">{item.title || item.folder}</span>
                          <Badge variant="outline" className="text-xs">{item.status}</Badge>
                        </div>
                        {item.error && (
                          <p className="text-xs text-destructive mt-1 pl-5">{item.error}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ZIP Upload (Future) */}
      <Card className="opacity-60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload ZIP Archive
            <Badge variant="outline" className="ml-2">Coming Soon</Badge>
          </CardTitle>
          <CardDescription>
            Upload a ZIP file containing MinerU-processed report folders
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className="border-2 border-dashed border-muted rounded-lg p-12 text-center cursor-not-allowed"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".zip"
              className="hidden"
              disabled
            />
            
            <Upload className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
            <h3 className="font-semibold text-lg text-muted-foreground">ZIP upload coming soon</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Use local processing for now
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Expected Format */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderOpen className="h-5 w-5" />
            Expected Folder Structure
          </CardTitle>
          <CardDescription>
            Each report should be in its own folder with MinerU outputs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
{`processed_reports_mineru/
├── Report_Name_1/
│   └── vlm/
│       ├── Report_Name_1.md          # Main content
│       ├── Report_Name_1_content_list.json
│       ├── Report_Name_1_origin.pdf  # Original PDF
│       └── images/                   # Extracted figures
│
├── Report_Name_2/
│   └── vlm/
│       ├── Report_Name_2.md
│       ├── Report_Name_2_content_list.json
│       └── ...
│
└── ...`}
          </pre>
        </CardContent>
      </Card>

      {/* Processing Info */}
      <Card>
        <CardHeader>
          <CardTitle>Processing Pipeline</CardTitle>
          <CardDescription>
            What happens when you process reports
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { step: 1, title: 'Parse', description: 'Read markdown content and extract title' },
              { step: 2, title: 'Infer', description: 'Detect source, year, category from filename' },
              { step: 3, title: 'Extract', description: 'LLM extracts findings, stats, quotes' },
              { step: 4, title: 'Store', description: 'Save to database with full intelligence' },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="h-10 w-10 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto mb-2 font-semibold">
                  {item.step}
                </div>
                <h4 className="font-medium">{item.title}</h4>
                <p className="text-xs text-muted-foreground mt-1">{item.description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
