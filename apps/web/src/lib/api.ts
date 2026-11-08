export type Profile = { display_name: string; email: string; target_locations: string; graduation_year: number | null };
export type Fact = { id: string; category: string; content: string; source: string; verified: boolean; created_at: string };
export type Status = "DISCOVERED" | "SHORTLISTED" | "SKIPPED" | "EXPIRED" | "WITHDRAWN";
export type Job = { id: string; url: string; company: string; title: string; location: string; description: string; deadline: string | null; start_date: string | null; eligibility_requirements: string; tracker_status: string | null; notes: string; sponsorship: "UNVERIFIED"; licensed_sponsor: boolean | null; status: Status; created_at: string };
export type JobInput = Pick<Job, "url" | "company" | "title" | "location" | "description" | "deadline" | "notes" | "start_date" | "eligibility_requirements">;
export type HistoryEvent = { id: string; from_status: string | null; to_status: string; created_at: string };
export const statuses: Status[] = ["DISCOVERED", "SHORTLISTED", "SKIPPED", "EXPIRED", "WITHDRAWN"];
export const label = (value: string) => value.toLowerCase().replaceAll("_", " ").replace(/^./, x => x.toUpperCase());

export async function api<T>(path: string, method = "GET", data?: unknown): Promise<T> {
  const response = await fetch(`/api/${path}`, {
    method, headers: { "Content-Type": "application/json" },
    body: data === undefined ? undefined : JSON.stringify(data), cache: "no-store",
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(response.status === 401 ? "The local API rejected the server credential. Restart the app using scripts/dev.py." :
      typeof error.detail === "string" ? error.detail : "Check the form fields and try again.");
  }
  return response.status === 204 ? undefined as T : response.json();
}

// Date-only deadlines use the applicant's UK calendar, never a UTC date conversion.
export function todayUK() { return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date()); }
export function daysUntil(value: string) { return Math.round((Date.parse(`${value}T00:00:00Z`) - Date.parse(`${todayUK()}T00:00:00Z`)) / 86400000); }
export function formatDate(value: string) { return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`)); }
export function active(job: Job) { return (job.status === "DISCOVERED" || job.status === "SHORTLISTED") && !(job.status === "DISCOVERED" && ["applied", "rejected", "offer", "withdrawn"].includes(job.tracker_status?.toLowerCase() ?? "")); }
