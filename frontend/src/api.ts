/** Typed wrappers over the scraper's HTTP API.
 *
 * Paths are relative: in production FastAPI serves this bundle from the same
 * origin, and in dev Vite proxies these routes to the server on :8000.
 */

export type EpubFile = {
  name: string
  size_bytes: number
  modified: string
}

export type JobStatus = "queued" | "running" | "done" | "failed"

export type Job = {
  id: string
  year: number
  month: number
  toc_url: string
  status: JobStatus
  step: string
  message: string
  articles_done: number
  articles_total: number
  filename: string | null
  created_at: string
  finished_at: string | null
}

/** An API call that came back with a non-2xx status. */
export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response))
  }
  return (await response.json()) as T
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === "string") {
      return body.detail
    }
  } catch {
    // Not JSON; fall through to the status text.
  }
  return `${response.status} ${response.statusText}`
}

export function listFiles(): Promise<EpubFile[]> {
  return request<EpubFile[]>("/files")
}

export function startScrape(year: number, month: number): Promise<Job> {
  return request<Job>("/scrape", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ year, month }),
  })
}

export function getJob(id: string): Promise<Job> {
  return request<Job>(`/jobs/${id}`)
}

/** Jobs still in flight, so a page reload can re-attach to a running scrape. */
export function listJobs(): Promise<Job[]> {
  return request<Job[]>("/jobs")
}

/** Filenames contain spaces, so they have to be encoded. */
export function downloadUrl(name: string): string {
  return `/files/${encodeURIComponent(name)}`
}
