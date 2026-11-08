"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export type Task = { id: string; kind: string; status: string; message: string | null; result: Record<string, unknown> | null; created_at: string };
type Candidate = { id: string; document_id: string; content: string; category: string | null };
type Settings = { backup_dir: string; target_roles: string[]; weights: Record<string, number> };
type SheetConfig = { spreadsheet_id: string; tab: string; header_row: number; mapping: Record<string, string>; is_test_copy: boolean; sync_every_minutes: number };
type SheetStatus = { config: SheetConfig | null; connected: boolean; missing: string[]; last_sync: string | null };

function Field({ name, children }: { name: string; children: ReactNode }) { return <label className="field"><span>{name}</span>{children}</label>; }
function ErrorText({ error }: { error: Error | null }) { return error ? <p role="alert" className="error">{error.message}</p> : null; }

export function SheetSyncTime() {
  const query = useQuery({ queryKey: ["sheet-status"], queryFn: () => api<SheetStatus>("sheets/config") });
  return <p className="sync-time">Last Sheet sync: {query.data?.last_sync ? new Date(query.data.last_sync.endsWith("Z") || /[+-]\d\d:\d\d$/.test(query.data.last_sync) ? query.data.last_sync : query.data.last_sync + "Z").toLocaleString("en-GB", { timeZone: "Europe/London" }) : "Not synced yet"}</p>;
}

export function URLImport() {
  const client = useQueryClient();
  const [url, setUrl] = useState("");
  const [html, setHtml] = useState("");
  const mutation = useMutation({ mutationFn: () => api<Task>("tasks/extract", "POST", { url, page_html: html }), onSuccess: () => { setUrl(""); setHtml(""); return client.invalidateQueries({ queryKey: ["tasks"] }); } });
  return <section className="panel form-panel url-import"><div className="panel-heading"><h2>Paste a job URL</h2><p className="muted small">Extract the listing in the background. Repeated URLs won’t create duplicate jobs.</p></div><form onSubmit={e => { e.preventDefault(); mutation.mutate(); }}><div className="url-input-row"><Field name="Job listing URL"><input type="url" required value={url} onChange={e => setUrl(e.target.value)} placeholder="https://employer.com/careers/job" /></Field><Button type="submit" disabled={mutation.isPending}>Add job</Button></div><details><summary>Paste page HTML instead of fetching</summary><Field name="Public job page HTML"><textarea rows={4} maxLength={1000000} value={html} onChange={e => setHtml(e.target.value)} placeholder="Optional: paste the HTML containing the vacancy’s JobPosting metadata." /></Field></details><ErrorText error={mutation.error} />{mutation.isSuccess && <p className="success" role="status">Job extraction queued. Follow its progress in Background tasks.</p>}</form></section>;
}

export function TaskList({ onSelect }: { onSelect: (id: string) => void }) {
  const client = useQueryClient();
  const tasks = useQuery({ queryKey: ["tasks"], queryFn: () => api<Task[]>("tasks"), refetchInterval: 1500 });
  const fingerprint = tasks.data?.map(t => `${t.id}:${t.status}`).join(",");
  useEffect(() => {
    for (const key of ["jobs", "candidates", "documents", "sheet-status", "matches"]) void client.invalidateQueries({ queryKey: [key] });
  }, [client, fingerprint]);
  const names: Record<string, string> = { extract_url: "Job URL extraction", parse_cv: "CV parsing", backup: "Backup and restore check", sheets_import: "Sheet import", sheets_sync: "Sheet sync", match_jobs: "Job matching", discover: "Job discovery" };
  return <section className="panel"><div className="panel-heading"><h2>Background tasks</h2><p className="small muted">Keep the app and worker running while tasks finish. Interrupted tasks require review.</p></div><ErrorText error={tasks.error} /><div className="task-list">{tasks.data?.slice(0, 12).map(task => <article className="task-row" key={task.id}><div><strong>{names[task.kind] ?? task.kind}</strong><span className={`badge task-${task.status.toLowerCase()}`}>{task.status.toLowerCase().replaceAll("_", " ")}</span>{task.message && <p role={task.status === "FAILED" ? "alert" : "status"}>{task.message}</p>}{typeof task.result?.job_id === "string" && <Button variant="ghost" onClick={() => onSelect(String(task.result!.job_id))}>View job</Button>}{typeof task.result?.candidates === "number" && <p>{task.result.candidates} candidates ready for review in My Profile.</p>}{task.result?.restore_verified === true && <p>Backup restored and verified. {String(task.result.archive)}</p>}{typeof task.result?.rows_preserved === "number" && <p>{task.result.rows_preserved} rows preserved · {String(task.result.cells_written ?? 0)} cells written · {String(task.result.warnings ?? 0)} warnings</p>}</div></article>)}{tasks.data?.length === 0 && <p className="muted">No tasks yet. Paste a job URL or upload a CV to begin.</p>}</div></section>;
}

export function CVReview() {
  const client = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [versionParent, setVersionParent] = useState("");
  const docs = useQuery({ queryKey: ["documents"], queryFn: () => api<{ id: string; format: string }[]>("documents") });
  const candidates = useQuery({ queryKey: ["candidates"], queryFn: () => api<Candidate[]>("candidates"), refetchInterval: 3000 });
  const upload = useMutation({ mutationFn: async () => {
    if (!file || file.size > 5000000) throw new Error("Choose a PDF, DOCX or TXT CV under 5 MB.");
    const format = file.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx", "txt"].includes(format ?? "")) throw new Error("Choose a PDF, DOCX or TXT CV.");
    const content = await new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(",")[1]); reader.onerror = () => reject(new Error("The selected file could not be read.")); reader.readAsDataURL(file); });
    return api<Task>("documents", "POST", { format, content_base64: content, parent_id: versionParent || null });
  }, onSuccess: () => { void client.invalidateQueries({ queryKey: ["tasks"] }); void client.invalidateQueries({ queryKey: ["documents"] }); } });
  const download = useMutation({ mutationFn: async (document: { id: string; format: string }) => {
    const response = await fetch(`/api/documents/${document.id}/download`, { cache: "no-store" });
    if (!response.ok) throw new Error("The CV could not be downloaded.");
    const url = URL.createObjectURL(await response.blob()); const anchor = window.document.createElement("a"); anchor.href = url; anchor.download = `cv-${document.id}.${document.format}`; anchor.click(); URL.revokeObjectURL(url);
  } });
  return <section className="panel form-panel"><div className="panel-heading"><h2>Upload and review your CV</h2><p className="muted small">Parsing stays local. Suggested facts are copied from your document and need your review.</p></div><form onSubmit={e => { e.preventDefault(); upload.mutate(); }}><Field name="CV file"><input type="file" accept=".pdf,.docx,.txt" required onChange={e => setFile(e.target.files?.[0] ?? null)} /></Field><Field name="Previous CV version (optional)"><select value={versionParent} onChange={e => setVersionParent(e.target.value)}><option value="">New master document</option>{docs.data?.map(doc => <option key={doc.id} value={doc.id}>{doc.id}</option>)}</select></Field><Button type="submit" disabled={upload.isPending}>{upload.isPending ? "Uploading…" : "Upload CV for local parsing"}</Button><ErrorText error={upload.error} />{upload.isSuccess && <p className="success" role="status">CV queued for local parsing. Candidates will appear below.</p>}</form><div className="candidate-list"><ErrorText error={candidates.error ?? docs.error ?? download.error} />{docs.data?.map(doc => <Button key={doc.id} variant="ghost" onClick={() => download.mutate(doc)}>Download CV {doc.id.slice(0, 8)}</Button>)}{candidates.data?.map(candidate => <CandidateCard key={candidate.id} candidate={candidate} />)}</div></section>;
}

function CandidateCard({ candidate }: { candidate: Candidate }) {
  const client = useQueryClient();
  const [content, setContent] = useState(candidate.content);
  const [category, setCategory] = useState(candidate.category ?? "");
  const [confirmed, setConfirmed] = useState(false);
  const mutation = useMutation({ mutationFn: (reject: boolean) => api(`candidates/${candidate.id}/${reject ? "reject" : "accept"}`, "POST", reject ? undefined : { content, category, source: `CV document ${candidate.document_id}`, verified: confirmed }), onSuccess: () => { void client.invalidateQueries({ queryKey: ["candidates"] }); void client.invalidateQueries({ queryKey: ["facts"] }); } });
  return <article className="fact-card"><p className="small muted">Extracted candidate · {candidate.document_id.slice(0, 8)}</p><Field name="Candidate fact"><textarea rows={3} maxLength={10000} value={content} onChange={e => { setContent(e.target.value); setConfirmed(false); }} /></Field><Field name="Candidate category"><select value={category} onChange={e => { setCategory(e.target.value); setConfirmed(false); }}><option value="">Choose a category</option>{["education", "experience", "project", "skill"].map(c => <option key={c} value={c}>{c}</option>)}</select></Field><label className="checkbox-label"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} />I have checked and confirm this exact fact.</label><ErrorText error={mutation.error} /><div className="form-actions"><Button variant="ghost" disabled={mutation.isPending} onClick={() => mutation.mutate(true)}>Discard candidate</Button><Button disabled={!category || !content.trim() || !confirmed || mutation.isPending} onClick={() => mutation.mutate(false)}>Save confirmed fact</Button></div></article>;
}

export function IntegrationSettings() {
  const preferences = useQuery({ queryKey: ["settings"], queryFn: () => api<Settings>("settings") });
  const sheet = useQuery({ queryKey: ["sheet-status"], queryFn: () => api<SheetStatus>("sheets/config") });
  return <div className="profile-grid"><div className="settings-stack"><section className="panel form-panel"><div className="panel-heading"><h2>Backups and preferences</h2></div>{preferences.data && <PreferencesForm data={preferences.data} />}<ErrorText error={preferences.error} /></section><section className="panel"><div className="panel-heading"><h2>Local access</h2><p className="muted">The dashboard opens directly on this computer. The API token stays in the local server’s private .env file and is never sent to the browser. Keep the app bound to localhost.</p></div></section></div><section className="panel form-panel"><div className="panel-heading"><h2>Google Sheets · test copy only</h2><p className="muted small">Read-only mode. The original tracker is blocked; no Sheet cells can be written.</p></div>{sheet.data && <SheetForm key={JSON.stringify(sheet.data.config)} status={sheet.data} />}<ErrorText error={sheet.error} /></section></div>;
}

function PreferencesForm({ data }: { data: Settings }) {
  const client = useQueryClient();
  const [directory, setDirectory] = useState(data.backup_dir);
  const [roles, setRoles] = useState(data.target_roles.join(", "));
  const mutation = useMutation({ mutationFn: () => api("settings", "PUT", { ...data, backup_dir: directory, target_roles: roles.split(",").map(r => r.trim()).filter(Boolean) }), onSuccess: () => client.invalidateQueries({ queryKey: ["settings"] }) });
  const backup = useMutation({ mutationFn: () => api<Task>("tasks/backup", "POST"), onSuccess: () => client.invalidateQueries({ queryKey: ["tasks"] }) });
  return <form onSubmit={e => { e.preventDefault(); mutation.mutate(); }}><Field name="Backup destination folder"><input value={directory} onChange={e => setDirectory(e.target.value)} placeholder="Absolute path outside storage" /></Field><p className="small muted">A daily backup runs while the app is open. Missed runs catch up once at startup. Each backup is restored and checked before success is reported. Keep your encryption key separately.</p><Field name="Preferred roles (comma-separated)"><input value={roles} onChange={e => setRoles(e.target.value)} /></Field><ErrorText error={mutation.error ?? backup.error} />{mutation.isSuccess && <p role="status" className="success">Settings saved.</p>}<div className="form-actions"><Button variant="outline" disabled={backup.isPending || !data.backup_dir} onClick={() => backup.mutate()}>Back up and verify restore</Button><Button type="submit" disabled={mutation.isPending}>Save settings</Button></div><details><summary>Restore a backup</summary><p className="small muted">From apps/api, run the backup restore command documented in README. Restore always uses a new directory and never overwrites your active data.</p></details></form>;
}

function SheetForm({ status }: { status: SheetStatus }) {
  const client = useQueryClient();
  const [form, setForm] = useState<SheetConfig>(status.config ?? { spreadsheet_id: "", tab: "", header_row: 1, mapping: { company: "Company", deadline: "Deadline", url: "Application Link", status: "Status", notes: "Notes" }, is_test_copy: false, sync_every_minutes: 0 });
  const save = useMutation({ mutationFn: () => api("sheets/config", "PUT", form), onSuccess: () => client.invalidateQueries({ queryKey: ["sheet-status"] }) });
  const connect = useMutation({ mutationFn: () => api<{ url: string }>("sheets/oauth/start", "POST"), onSuccess: data => window.location.assign(data.url) });
  const run = useMutation({ mutationFn: (operation: string) => api<Task>(`tasks/sheets/${operation}`, "POST"), onSuccess: () => client.invalidateQueries({ queryKey: ["tasks"] }) });
  return <form onSubmit={e => { e.preventDefault(); save.mutate(); }}><p className="notice">{status.connected ? "Google is connected." : "Google is not connected."}{status.missing.length > 0 && ` Configure privately: ${status.missing.join(", ")}.`}</p><Field name="Test-copy spreadsheet ID"><input required value={form.spreadsheet_id} onChange={e => setForm({ ...form, spreadsheet_id: e.target.value })} /></Field><div className="form-grid"><Field name="Sheet tab name"><input required value={form.tab} onChange={e => setForm({ ...form, tab: e.target.value })} /></Field><Field name="Header row number"><input type="number" min={1} max={100} value={form.header_row} onChange={e => setForm({ ...form, header_row: Number(e.target.value) })} /></Field></div><h3>Column headers</h3>{Object.entries(form.mapping).map(([key, header]) => <Field key={key} name={`${key === "url" ? "Job URL" : key} header`}><input required value={header} onChange={e => setForm({ ...form, mapping: { ...form.mapping, [key]: e.target.value } })} /></Field>)}<Field name="Automatic read-only import interval (minutes, 0 disables)"><input type="number" min={0} max={1440} value={form.sync_every_minutes} onChange={e => setForm({ ...form, sync_every_minutes: Number(e.target.value) })} /></Field><label className="checkbox-label"><input type="checkbox" required checked={form.is_test_copy} onChange={e => setForm({ ...form, is_test_copy: e.target.checked })} />This is a separate test copy, not my original tracker.</label><ErrorText error={save.error ?? connect.error ?? run.error} /><div className="form-actions"><Button type="submit" disabled={save.isPending}>Save Sheet mapping</Button><Button variant="outline" disabled={connect.isPending || status.missing.length > 0} onClick={() => connect.mutate()}>Connect Google</Button></div><div className="form-actions"><Button variant="outline" disabled={!status.config || !status.connected || run.isPending} onClick={() => run.mutate("import")}>Import test copy</Button><span className="small muted">Write access is disabled pending verified read-only import and your approval.</span></div></form>;
}

export function Declarations() {
  const client = useQueryClient();
  const [category, setCategory] = useState("right_to_work");
  const [question, setQuestion] = useState(""); const [value, setValue] = useState(""); const [confirmed, setConfirmed] = useState(false);
  const records = useQuery({ queryKey: ["declarations"], queryFn: () => api<{ id: string; question: string; value: string }[]>("declarations") });
  const save = useMutation({ mutationFn: () => api("declarations", "POST", { category, question, value, confirmed }), onSuccess: () => { setQuestion(""); setValue(""); setConfirmed(false); return client.invalidateQueries({ queryKey: ["declarations"] }); } });
  const remove = useMutation({ mutationFn: (id: string) => api(`declarations/${id}`, "DELETE"), onSuccess: () => client.invalidateQueries({ queryKey: ["declarations"] }) });
  return <section className="panel form-panel"><div className="panel-heading"><h2>Fixed declarations</h2><p className="muted small">Optional owner-confirmed answers only. No AI drafts or infers these values. Unknown answers remain unknown.</p></div><form onSubmit={e => { e.preventDefault(); save.mutate(); }}><Field name="Declaration category"><select value={category} onChange={e => { setCategory(e.target.value); setConfirmed(false); }}>{["right_to_work", "sponsorship", "convictions", "disability", "diversity", "consent", "identity"].map(c => <option key={c} value={c}>{c.replaceAll("_", " ")}</option>)}</select></Field><Field name="Exact question"><input required maxLength={500} value={question} onChange={e => { setQuestion(e.target.value); setConfirmed(false); }} /></Field><Field name="Your fixed answer"><textarea required maxLength={2000} value={value} onChange={e => { setValue(e.target.value); setConfirmed(false); }} /></Field><label className="checkbox-label"><input type="checkbox" required checked={confirmed} onChange={e => setConfirmed(e.target.checked)} />I confirm this answer for this exact question.</label><Button type="submit" disabled={!confirmed || save.isPending}>Save confirmed declaration</Button><ErrorText error={save.error ?? records.error ?? remove.error} /></form><div className="candidate-list">{records.data?.map(record => <article className="fact-card" key={record.id}><strong>{record.question}</strong><p className="preserve">{record.value}</p><Button variant="ghost" disabled={remove.isPending} onClick={() => { if (window.confirm("Delete this fixed declaration?")) remove.mutate(record.id); }}>Delete declaration</Button></article>)}</div></section>;
}
