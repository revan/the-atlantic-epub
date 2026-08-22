/** The magazine's issues, as a month-by-month list. */

export type Issue = {
  year: number
  /** 1-12. */
  month: number
}

/** The Atlantic Monthly's first issue. */
export const FIRST_ISSUE: Issue = { year: 1857, month: 11 }

/** Stable key for an issue, e.g. "2026-09". */
export function issueKey({ year, month }: Issue): string {
  return `${year}-${String(month).padStart(2, "0")}`
}

/**
 * Where the card list starts: the month after the one `now` falls in.
 *
 * The magazine publishes ahead of the calendar, so next month's issue is
 * generally out — or close enough to be worth a card — before it arrives.
 */
export function nextIssue(now: Date): Issue {
  const month = now.getMonth() + 2
  return month > 12 ? { year: now.getFullYear() + 1, month: 1 } : { year: now.getFullYear(), month }
}

/** Negative when `a` is the older issue, positive when it is the newer. */
export function compareIssues(a: Issue, b: Issue): number {
  return a.year - b.year || a.month - b.month
}

/**
 * Every issue month from `from` back to November 1857, newest first.
 *
 * Not every month has an issue — the magazine combines months in recent years
 * and varied in its early decades — so some of these will fail to scrape.
 */
export function enumerateMonths(from: Issue): Issue[] {
  const issues: Issue[] = []
  let { year, month } = from

  while (compareIssues({ year, month }, FIRST_ISSUE) >= 0) {
    issues.push({ year, month })
    month -= 1
    if (month === 0) {
      month = 12
      year -= 1
    }
  }
  return issues
}

/**
 * The EPUB the pipeline writes for an issue.
 *
 * Must match `url_to_filename` in `magazine_scraper/pipeline.py` exactly,
 * spaces included — the frontend joins files to months by this string.
 */
export function epubFilename(issue: Issue): string {
  return `The Atlantic ${issueKey(issue)}.epub`
}

const MONTH_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
]

/** Human-readable issue name, e.g. "September 2026". */
export function formatIssue({ year, month }: Issue): string {
  return `${MONTH_NAMES[month - 1]} ${year}`
}
