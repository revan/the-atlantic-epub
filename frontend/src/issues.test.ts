import { describe, expect, it } from "vitest"

import {
  compareIssues,
  enumerateMonths,
  epubFilename,
  formatIssue,
  issueKey,
  nextIssue,
} from "./issues"

describe("enumerateMonths", () => {
  it("starts at the current month and ends at the first issue", () => {
    const issues = enumerateMonths({ year: 2026, month: 8 })

    expect(issues[0]).toEqual({ year: 2026, month: 8 })
    expect(issues.at(-1)).toEqual({ year: 1857, month: 11 })
  })

  it("counts every month between the two ends", () => {
    // Nov and Dec 1857, then 1858-2025 inclusive, then Jan-Aug 2026.
    const issues = enumerateMonths({ year: 2026, month: 8 })

    expect(issues).toHaveLength(2 + (2025 - 1858 + 1) * 12 + 8)
  })

  it("stops at November when asked for the first issue's month", () => {
    expect(enumerateMonths({ year: 1857, month: 11 })).toEqual([{ year: 1857, month: 11 }])
  })

  it("is empty before the first issue", () => {
    expect(enumerateMonths({ year: 1857, month: 10 })).toEqual([])
  })

  it("is strictly descending with no gaps", () => {
    const issues = enumerateMonths({ year: 2026, month: 8 })

    for (let i = 1; i < issues.length; i += 1) {
      const previous = issues[i - 1]
      const current = issues[i]
      const expected =
        previous.month === 1
          ? { year: previous.year - 1, month: 12 }
          : { year: previous.year, month: previous.month - 1 }
      expect(current).toEqual(expected)
    }
  })
})

describe("epubFilename", () => {
  it("matches the pipeline's naming, with a zero-padded month", () => {
    expect(epubFilename({ year: 2026, month: 9 })).toBe("The Atlantic 2026-09.epub")
    expect(epubFilename({ year: 2026, month: 12 })).toBe("The Atlantic 2026-12.epub")
    expect(epubFilename({ year: 1857, month: 11 })).toBe("The Atlantic 1857-11.epub")
  })
})

describe("issueKey and formatIssue", () => {
  it("keys on zero-padded year-month", () => {
    expect(issueKey({ year: 1900, month: 1 })).toBe("1900-01")
  })

  it("names the month", () => {
    expect(formatIssue({ year: 2026, month: 9 })).toBe("September 2026")
    expect(formatIssue({ year: 1857, month: 11 })).toBe("November 1857")
  })
})

describe("nextIssue", () => {
  it("is the month after the calendar month", () => {
    expect(nextIssue(new Date(2026, 7, 22))).toEqual({ year: 2026, month: 9 })
    expect(nextIssue(new Date(2026, 0, 1))).toEqual({ year: 2026, month: 2 })
  })

  it("rolls over into January of the next year from December", () => {
    expect(nextIssue(new Date(2026, 11, 31))).toEqual({ year: 2027, month: 1 })
  })
})

describe("compareIssues", () => {
  it("orders by year then month", () => {
    expect(compareIssues({ year: 2026, month: 9 }, { year: 2026, month: 8 })).toBeGreaterThan(0)
    expect(compareIssues({ year: 1999, month: 12 }, { year: 2000, month: 1 })).toBeLessThan(0)
    expect(compareIssues({ year: 2026, month: 8 }, { year: 2026, month: 8 })).toBe(0)
  })
})
