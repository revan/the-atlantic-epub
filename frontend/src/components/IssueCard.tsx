import { Download, Loader2, RefreshCw } from "lucide-react"

import type { EpubFile, Job } from "@/api"
import { downloadUrl } from "@/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardHeader, CardTitle } from "@/components/ui/card"
import type { Issue } from "@/issues"
import { formatIssue } from "@/issues"

type IssueCardProps = {
  issue: Issue
  /** The EPUB on disk, if this issue has been scraped. */
  file: EpubFile | undefined
  /** The most recent scrape of this issue, if the server still remembers one. */
  job: Job | undefined
  /** A request that never became a job, e.g. a 409 from a duplicate scrape. */
  error: string | undefined
  onScrape: (issue: Issue) => void
}

/** Bytes as megabytes, e.g. "1.4 MB". */
function formatSize(bytes: number): string {
  return `${(bytes / 1_000_000).toFixed(1)} MB`
}

const SCRAPED_ON = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
})

/** What a running job is doing, e.g. "scraping articles 12/34". */
function progressLabel(job: Job): string {
  if (job.status === "queued") {
    return "queued"
  }
  if (job.articles_total > 0) {
    return `${job.step} ${job.articles_done}/${job.articles_total}`
  }
  return job.step
}

export function IssueCard({ issue, file, job, error, onScrape }: IssueCardProps) {
  const active = job !== undefined && (job.status === "queued" || job.status === "running")
  const failure = error ?? (job?.status === "failed" ? job.message : undefined)

  return (
    <Card className="gap-3 py-4">
      <CardHeader className="items-center gap-3">
        <CardTitle className="text-base font-medium tabular-nums">{formatIssue(issue)}</CardTitle>

        {file ? (
          <div className="col-start-1 row-start-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
            <Badge variant="secondary">Scraped</Badge>
            <span className="font-mono text-xs">{file.name}</span>
            <span>{SCRAPED_ON.format(new Date(file.modified))}</span>
            <span>{formatSize(file.size_bytes)}</span>
          </div>
        ) : (
          <div className="col-start-1 row-start-2 text-sm text-muted-foreground">
            {active ? progressLabel(job) : "Not scraped"}
          </div>
        )}

        {failure !== undefined && (
          <div className="col-start-1 row-start-3 flex items-center gap-2 text-sm">
            <Badge variant="destructive">Failed</Badge>
            <span className="text-muted-foreground">{failure}</span>
          </div>
        )}

        <CardAction className="flex items-center gap-2 self-center">
          {file && (
            <Button asChild size="sm" variant="default">
              <a href={downloadUrl(file.name)} download>
                <Download aria-hidden />
                Download
              </a>
            </Button>
          )}
          <Button
            size="sm"
            variant={file ? "ghost" : "outline"}
            disabled={active}
            onClick={() => onScrape(issue)}
          >
            {active ? (
              <>
                <Loader2 className="animate-spin" aria-hidden />
                Scraping
              </>
            ) : file ? (
              <>
                <RefreshCw aria-hidden />
                Re-scrape
              </>
            ) : (
              "Scrape"
            )}
          </Button>
        </CardAction>
      </CardHeader>
    </Card>
  )
}
