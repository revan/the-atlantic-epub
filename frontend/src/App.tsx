import { useCallback, useEffect, useMemo, useState } from "react"

import type { EpubFile, Job } from "@/api"
import { getJob, listFiles, listJobs, startScrape } from "@/api"
import { IssueCard } from "@/components/IssueCard"
import { Skeleton } from "@/components/ui/skeleton"
import type { Issue } from "@/issues"
import { enumerateMonths, epubFilename, issueKey, nextIssue } from "@/issues"

/** Cards added each time the bottom of the list comes into view. */
const PAGE_SIZE = 60
/** How often to re-check jobs that are still running. */
const POLL_MS = 2000
/** How close to the bottom of the page loads the next page of cards. */
const LOAD_MARGIN_PX = 600

function isActive(job: Job): boolean {
  return job.status === "queued" || job.status === "running"
}

export default function App() {
  // Newest first, from next month back to the magazine's first issue.
  const issues = useMemo(() => enumerateMonths(nextIssue(new Date())), [])

  const [files, setFiles] = useState<Map<string, EpubFile> | null>(null)
  const [jobs, setJobs] = useState<Map<string, Job>>(new Map())
  const [errors, setErrors] = useState<Map<string, string>>(new Map())
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)

  const refreshFiles = useCallback(async () => {
    const listed = await listFiles()
    setFiles(new Map(listed.map((file) => [file.name, file])))
  }, [])

  // Durable state: which EPUBs exist on the volume.
  useEffect(() => {
    void refreshFiles()
  }, [refreshFiles])

  // Re-attach to scrapes already in flight, so a reload keeps showing progress.
  useEffect(() => {
    void listJobs().then((all) => {
      const active = all.filter(isActive)
      if (active.length > 0) {
        setJobs(new Map(active.map((job) => [issueKey(job), job])))
      }
    })
  }, [])

  // Poll only while something is running. `activeIds` is a string so the effect
  // restarts when the set of running jobs changes, not on every progress tick.
  const activeIds = [...jobs.values()].filter(isActive).map((job) => job.id).join(",")
  useEffect(() => {
    if (activeIds === "") {
      return
    }
    const ids = activeIds.split(",")
    const timer = setInterval(() => {
      for (const id of ids) {
        void getJob(id).then((updated) => {
          setJobs((latest) => new Map(latest).set(issueKey(updated), updated))
          if (updated.status === "done") {
            void refreshFiles()
          }
        })
      }
    }, POLL_MS)
    return () => clearInterval(timer)
  }, [activeIds, refreshFiles])

  // Infinite scroll back toward 1857. A page of cards is far taller than any
  // viewport, so reaching the bottom always takes a scroll — no initial check.
  useEffect(() => {
    const extend = () => {
      const distanceToBottom =
        document.documentElement.scrollHeight - window.scrollY - window.innerHeight
      if (distanceToBottom < LOAD_MARGIN_PX) {
        setVisibleCount((count) => Math.min(count + PAGE_SIZE, issues.length))
      }
    }
    window.addEventListener("scroll", extend, { passive: true })
    window.addEventListener("resize", extend)
    return () => {
      window.removeEventListener("scroll", extend)
      window.removeEventListener("resize", extend)
    }
  }, [issues.length])

  const onScrape = useCallback(async (issue: Issue) => {
    const key = issueKey(issue)
    setErrors((current) => {
      const next = new Map(current)
      next.delete(key)
      return next
    })
    try {
      const job = await startScrape(issue.year, issue.month)
      setJobs((current) => new Map(current).set(key, job))
    } catch (error) {
      // A 409 means the server already has this month queued or running.
      setErrors((current) => new Map(current).set(key, describe(error)))
    }
  }, [])

  const scrapedCount = files?.size ?? 0
  const visible = issues.slice(0, visibleCount)

  return (
    <div className="mx-auto min-h-screen w-full max-w-3xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">The Atlantic</h1>
        <p className="mt-1 text-muted-foreground">
          {files === null
            ? "Loading issues…"
            : `${scrapedCount} ${scrapedCount === 1 ? "issue" : "issues"} scraped`}
        </p>
      </header>

      <div className="flex flex-col gap-3">
        {files === null
          ? Array.from({ length: 8 }, (_, i) => <Skeleton key={i} className="h-[86px] w-full" />)
          : visible.map((issue) => {
              const key = issueKey(issue)
              return (
                <IssueCard
                  key={key}
                  issue={issue}
                  file={files.get(epubFilename(issue))}
                  job={jobs.get(key)}
                  error={errors.get(key)}
                  onScrape={onScrape}
                />
              )
            })}
      </div>
    </div>
  )
}

function describe(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}
