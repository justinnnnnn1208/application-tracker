"use client";

import { useState, type FormEvent, type ReactNode } from "react";
import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CVReview, Declarations, IntegrationSettings, TaskList, URLImport, SheetSyncTime } from "@/components/workflows";
import { Button } from "@/components/ui/button";
import { active, api, daysUntil, formatDate, label, statuses, type Fact, type HistoryEvent, type Job, type JobInput, type Profile, type Status } from "@/lib/api";

function Arrow() { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M6 18 18 6M6 6h12v12" /></svg>; }

type View = "Dashboard" | "Jobs" | "Deadlines" | "My Profile" | "Settings";
const blankProfile: Profile = { display_name: "", email: "", target_locations: "", graduation_year: null };

function Icon({ name }: { name: string }) {
  const paths: Record<string, ReactNode> = {
    Dashboard: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    "Jobs": <><rect x="3" y="7" width="18" height="14" rx="2" /><path d="M8 7V3h8v4M3 12h18M10 12v3h4v-3" /></>,
    Deadlines: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M7 3v4m10-4v4M3 11h18m-13 5h2m4 0h2" /></>,
    "My Profile": <><circle cx="12" cy="8" r="4" /><path d="M4 21v-2a8 8 0 0 1 16 0v2" /></>,
    Settings: <><path d="m9 3 1-1h4l1 1 1 3 3 1 2 3v4l-2 3-3 1-1 3-1 1h-4l-1-1-1-3-3-1-2-3v-4l2-3 3-1z" /><circle cx="12" cy="12" r="3" /></>,
  };
  return <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">{paths[name] ?? <path d="m7 12 3 3 7-7M12 2l9 4v6c0 5-9 10-9 10S3 17 3 12V6z" />}</svg>;
}

function Field({ label: text, children }: { label: string; children: ReactNode }) {
  return <label className="field"><span>{text}</span>{children}</label>;
}
function ErrorMessage({ error }: { error: Error | null }) { return error ? <p className="error" role="alert">{error.message}</p> : null; }

export function Tracker() {
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 10000 } } }));
  return <QueryClientProvider client={client}><Workspace /></QueryClientProvider>;
}

function Workspace() {
  const [view, setView] = useState<View>("Dashboard");
  const [adding, setAdding] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => api<Job[]>("jobs"), refetchInterval: 60000 });
  const profile = useQuery({ queryKey: ["profile"], queryFn: () => api<Profile>("profile") });
  const list = jobs.data ?? [];
  const chosen = list.find(job => job.id === selected);
  const closing = list.filter(job => active(job) && job.deadline && daysUntil(job.deadline) >= 0 && daysUntil(job.deadline) <= 7)
    .sort((a, b) => a.deadline!.localeCompare(b.deadline!));
  const firstName = profile.data?.display_name.trim().split(/\s+/)[0];
  function navigate(next: View) { setView(next); setSelected(null); setAdding(false); }
  const subtitles: Record<View, string> = {
    Dashboard: "Your job search, at a glance.",
    Jobs: "All your saved roles. Find the right one to focus on next.",
    Deadlines: "Keep track of what’s coming up, using the UK calendar.",
    "My Profile": "Upload your CV, review your facts, and keep your details accurate.",
    Settings: "Manage your Sheet connection, backups, and local workspace.",
  };
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="wordmark"><span className="brand-mark"><Icon name="Jobs" /></span><span>Job Tracker</span></div>
      <p className="workspace-label">PERSONAL WORKSPACE</p>
      <nav aria-label="Main navigation">
        {(["Dashboard", "Jobs", "Deadlines", "My Profile", "Settings"] as View[]).map(item => <button key={item} aria-label={item}
          aria-current={view === item ? "page" : undefined} className={view === item ? "nav-item current" : "nav-item"} onClick={() => navigate(item)}>
          <Icon name={item} /><span>{item}</span>{item === "Jobs" && <span className="nav-count" aria-hidden="true">{list.length}</span>}
        </button>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="safety-card"><Icon name="shield" /><strong>You stay in control</strong><p>Track opportunities here.<br />Apply when you’re ready.</p><span>Automatic submission is off</span></div>
        <div className="owner"><span className="avatar">{firstName?.[0]?.toUpperCase() ?? "Y"}</span><div><strong>{firstName ?? "Your workspace"}</strong><small>Local to this computer</small></div></div>
      </div>
    </aside>
    <div className="main-wrap">
      <main className="main-content">
        <header className="page-heading">
          <div><h1>{view}</h1><p className="muted">{subtitles[view]}</p>{view === "Dashboard" && <SheetSyncTime />}</div>
          {view === "Dashboard" ? <URLImport compact /> : (view === "Jobs" || view === "Deadlines") && <Button onClick={() => { setAdding(true); setSelected(null); }}>＋ Add a job</Button>}
        </header>
        <ErrorMessage error={jobs.error} /><ErrorMessage error={profile.error} />
        {adding ? <JobForm onDone={() => setAdding(false)} onCancel={() => setAdding(false)} />
          : chosen ? <JobDetail key={chosen.id} job={chosen} onBack={() => setSelected(null)} />
          : view === "My Profile" ? <div className="page-stack"><CVReview /><ProfileEditor profile={profile.data} /><Declarations /><TaskList onSelect={setSelected} /></div>
          : view === "Settings" ? <div className="page-stack"><IntegrationSettings /><TaskList onSelect={setSelected} /></div>
          : jobs.isPending ? <div className="panel empty" role="status">Loading your workspace…</div>
          : jobs.isError ? <section className="panel empty"><h2>Your jobs couldn’t be loaded</h2><p>Check that the local API is running, then try again.</p><Button variant="outline" onClick={() => void jobs.refetch()}>Try again</Button></section>
          : view === "Dashboard" ? <>
            <div className="stats-grid">
              <Stat number={list.length} text="Jobs tracked" detail="Saved in your tracker" />
              <Stat number={closing.length} text="Closing in 7 days" detail="Active roles with a known deadline" />
              <Stat number={0} text="Applied" detail="Confirmed submissions only" />
            </div>
            <JobList jobs={closing} onSelect={setSelected} onAdd={() => setAdding(true)} overview />
            <TaskList onSelect={setSelected} />
            <p className="overview-footer"><Icon name="shield" />Sponsorship stays Unverified until role-specific evidence is recorded. A sponsor licence alone is not confirmation.</p>
          </> : view === "Deadlines" ? <DeadlineList jobs={list} onSelect={setSelected} />
          : <JobList jobs={list} onSelect={setSelected} onAdd={() => setAdding(true)} overview={false} />}
      </main>
      <footer className="app-footer"><span>Job Tracker · Personal workspace</span><span>Local only · Automatic submission off</span></footer>
    </div>
  </div>;
}

function Stat({ number, text, detail }: { number: number; text: string; detail: string }) {
  return <div className="stat panel"><span>{text}</span><strong>{number}</strong><small>{detail}</small></div>;
}

function Deadline({ value }: { value: string | null }) {
  if (!value) return <span className="muted">Not provided</span>;
  const days = daysUntil(value);
  return <div className="deadline-cell"><span>{formatDate(value)}</span><small className={days <= 7 ? "urgent" : "muted"}>{days < 0 ? "Deadline passed" : days === 0 ? "Due today" : days === 1 ? "Due tomorrow" : `${days} days left`}</small></div>;
}

function JobList({ jobs, onSelect, onAdd, overview }: { jobs: Job[]; onSelect: (id: string) => void; onAdd: () => void; overview: boolean }) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("ALL");
  const [deadline, setDeadline] = useState("ALL");
  const [sponsorship, setSponsorship] = useState("ALL");
  const [sort, setSort] = useState("deadline");
  const filtered = jobs.filter(job => {
    const matchesSearch = `${job.company} ${job.title} ${job.location} ${job.notes}`.toLowerCase().includes(search.trim().toLowerCase());
    const days = job.deadline ? daysUntil(job.deadline) : null;
    const matchesDeadline = deadline === "ALL" || (deadline === "unknown" ? days === null : deadline === "past" ? days !== null && days < 0 : days !== null && days >= 0 && days <= Number(deadline));
    return matchesSearch && (status === "ALL" || job.status === status) && matchesDeadline && (sponsorship === "ALL" || job.sponsorship === sponsorship);
  }).sort((a, b) => sort === "company" ? a.company.localeCompare(b.company) : sort === "newest" ? b.created_at.localeCompare(a.created_at) : (a.deadline ?? "9999").localeCompare(b.deadline ?? "9999") || a.company.localeCompare(b.company));
  return <section className="panel jobs-panel">
    <div className="panel-heading"><div><h2>{overview ? "Closing soon" : "Saved jobs"}<span className="count-pill">{jobs.length}</span></h2><p className="muted small">{overview ? "Active opportunities closing in the next 7 days." : "Search, filter, and organise your opportunities."}</p></div></div>
    {!overview && <div className="table-tools">
      <Field label="Search"><input aria-label="Search jobs" placeholder="Company, role, location or notes" value={search} onChange={event => setSearch(event.target.value)} /></Field>
      <Field label="Status"><select aria-label="Filter by status" value={status} onChange={event => setStatus(event.target.value)}><option value="ALL">All statuses</option>{statuses.map(value => <option key={value} value={value}>{label(value)}</option>)}</select></Field>
      <Field label="Deadline"><select aria-label="Filter by deadline" value={deadline} onChange={event => setDeadline(event.target.value)}><option value="ALL">All deadlines</option><option value="7">Closing in 7 days</option><option value="30">Closing in 30 days</option><option value="past">Deadline passed</option><option value="unknown">No deadline provided</option></select></Field>
      <Field label="Sponsorship"><select aria-label="Filter by sponsorship" value={sponsorship} onChange={event => setSponsorship(event.target.value)}><option value="ALL">All sponsorship</option><option value="UNVERIFIED">Unverified</option></select></Field>
      <Field label="Sort"><select aria-label="Sort jobs" value={sort} onChange={event => setSort(event.target.value)}><option value="deadline">Deadline (soonest)</option><option value="newest">Newest first</option><option value="company">Company (A–Z)</option></select></Field>
    </div>}
    {filtered.length ? <div className="table-scroll" role="region" aria-label={overview ? "Closing soon jobs" : "Saved jobs"} tabIndex={0}><table>
      <thead><tr><th>Role</th><th>Company and location</th><th>Deadline</th><th>Sponsorship</th><th>Status</th><th><span className="sr-only">Details</span></th></tr></thead>
      <tbody>{filtered.map(job => <tr key={job.id}>
        <td><button className="job-link" onClick={() => onSelect(job.id)}>{job.title}</button></td>
        <td><div className="company-cell"><strong>{job.company}</strong><span>{job.location || "Location not provided"}</span></div></td>
        <td><Deadline value={job.deadline} /></td><td><span className="badge unverified">Unverified</span></td>
        <td><span className={`badge status-${job.status.toLowerCase()}`}>{label(job.status)}</span></td>
        <td><button className="row-arrow" onClick={() => onSelect(job.id)} aria-label={`View ${job.title} at ${job.company}`}><Arrow /></button></td>
      </tr>)}</tbody>
    </table></div> : <div className="empty"><div className="empty-icon"><Icon name={overview ? "Deadlines" : "Jobs"} /></div>
      <h3>{overview ? "No jobs closing in the next 7 days" : jobs.length ? "No jobs match these filters" : "Your tracker is ready"}</h3>
      <p>{overview ? "Add a role with a deadline to see it here. All saved jobs are available in Jobs." : jobs.length ? "Try another search, status, or deadline." : "Paste a job URL on the Dashboard, or add your first job below."}</p>
      {!jobs.length && <Button variant="outline" onClick={onAdd}>＋ Add your first job</Button>}
    </div>}
    <div className="table-footer"><span>{filtered.length} {filtered.length === 1 ? "job" : "jobs"}{!overview && ` of ${jobs.length}`}</span><span>Saved on this computer</span></div>
  </section>;
}

function DeadlineList({ jobs, onSelect }: { jobs: Job[]; onSelect: (id: string) => void }) {
  const dated = jobs.filter(j => active(j) && j.deadline).sort((a, b) => a.deadline!.localeCompare(b.deadline!));
  const groups = [
    { name: "Needs attention · deadline passed", items: dated.filter(j => daysUntil(j.deadline!) < 0) },
    { name: "Coming up · next 7 days", items: dated.filter(j => daysUntil(j.deadline!) >= 0 && daysUntil(j.deadline!) <= 7) },
    { name: "On the horizon", items: dated.filter(j => daysUntil(j.deadline!) > 7) },
    { name: "Deadline to check", items: jobs.filter(j => active(j) && !j.deadline) },
  ];
  return <section className="panel deadline-panel"><div className="panel-heading"><h2>Deadline reminders</h2><p className="muted small">In-app reminders for active roles, using the UK calendar. No external notifications yet.</p></div>{!jobs.some(active) && <div className="empty"><Icon name="Deadlines" /><h3>A clear calendar.</h3><p>Add an opportunity with a deadline to see it here.</p></div>}{groups.filter(g => g.items.length).map(group => <div className="deadline-group" key={group.name}><h3>{group.name}<span className="count-pill">{group.items.length}</span></h3>{group.items.map(job => <button className="deadline-row" key={job.id} onClick={() => onSelect(job.id)}><span><strong>{job.title}</strong><small>{job.company} · {job.location || "Location not provided"}</small></span><Deadline value={job.deadline} /><span><Arrow /></span></button>)}</div>)}</section>;
}

function JobForm({ job, onDone, onCancel }: { job?: Job; onDone: () => void; onCancel: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<JobInput>(job ? { url: job.url, company: job.company, title: job.title, location: job.location, description: job.description, deadline: job.deadline, notes: job.notes, start_date: job.start_date, eligibility_requirements: job.eligibility_requirements } : { url: "", company: "", title: "", location: "", description: "", deadline: null, notes: "", start_date: null, eligibility_requirements: "" });
  const mutation = useMutation({ mutationFn: () => api<Job>(job ? `jobs/${job.id}` : "jobs", job ? "PUT" : "POST", form), onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["jobs"] }); onDone(); } });
  const field = (key: keyof JobInput) => ({ value: form[key] ?? "", onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setForm({ ...form, [key]: (key === "deadline" || key === "start_date") ? e.target.value || null : e.target.value }) });
  return <section className="panel form-panel"><div className="panel-heading"><h2>{job ? "Edit opportunity" : "Add an opportunity"}</h2><p className="muted small">Enter verified details from the listing, or use the Dashboard URL input for extraction.</p></div><form onSubmit={e => { e.preventDefault(); mutation.mutate(); }}><Field label="Job URL *"><input type="url" required maxLength={2048} placeholder="https://company.com/careers/graduate-role" {...field("url")} /></Field><div className="form-grid"><Field label="Company *"><input required maxLength={200} {...field("company")} /></Field><Field label="Role title *"><input required maxLength={300} {...field("title")} /></Field><Field label="Location"><input maxLength={300} placeholder="As stated in the listing" {...field("location")} /></Field><Field label="Application deadline"><input type="date" {...field("deadline")} /></Field></div><Field label="Job description"><textarea rows={6} maxLength={100000} placeholder="Paste the original job description for reference" {...field("description")} /></Field><div className="form-grid"><Field label="Role start date"><input type="date" {...field("start_date")} /></Field><Field label="Eligibility requirements"><textarea rows={2} maxLength={20000} {...field("eligibility_requirements")} /></Field></div><Field label="Your notes"><textarea rows={3} maxLength={10000} {...field("notes")} /></Field><div className="notice">Sponsorship is saved as <strong>Unverified</strong>. Nothing is inferred from the company or job description.</div><ErrorMessage error={mutation.error} /><div className="form-actions"><Button variant="outline" onClick={onCancel} disabled={mutation.isPending}>Cancel</Button><Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Saving…" : "Save opportunity"}</Button></div></form></section>;
}

function JobDetail({ job, onBack }: { job: Job; onBack: () => void }) {
  const [editing, setEditing] = useState(false);
  const queryClient = useQueryClient();
  const history = useQuery({ queryKey: ["events", job.id], queryFn: () => api<HistoryEvent[]>(`jobs/${job.id}/events`) });
  const mutation = useMutation({ mutationFn: (status: Status) => api<Job>(`jobs/${job.id}/status`, "PATCH", { status, expected_status: job.status }), onSuccess: async () => { await Promise.all([queryClient.invalidateQueries({ queryKey: ["jobs"] }), queryClient.invalidateQueries({ queryKey: ["events", job.id] })]); } });
  if (editing) return <JobForm job={job} onDone={() => setEditing(false)} onCancel={() => setEditing(false)} />;
  return <><Button variant="ghost" onClick={onBack}>Back to opportunities</Button><div className="detail-grid"><section className="panel detail-panel"><div className="detail-heading"><span className="company-avatar large">{job.company[0]}</span><div><p className="muted">{job.company}</p><h2>{job.title}</h2><p className="muted">{job.location || "Location not provided"}</p></div></div><div className="detail-actions"><a href={job.url} target="_blank" rel="noopener noreferrer" className="button button-outline">Open job listing <Arrow /></a><Button variant="ghost" onClick={() => setEditing(true)}>Edit details</Button></div><h3>Job description</h3><p className="preserve">{job.description || "No description saved yet."}</p><h3>Start date and eligibility</h3><p className="preserve">{job.start_date ? formatDate(job.start_date) : "Start date not provided"}</p><p className="preserve">{job.eligibility_requirements || "Eligibility requirements not extracted yet."}</p>{job.tracker_status && <p className="notice">Imported tracker history is preserved separately and needs confirmation evidence before this app can mark an application as submitted.</p>}<h3>Your notes</h3><p className="preserve">{job.notes || "No notes yet."}</p><h3>History</h3><ErrorMessage error={history.error} />{history.isPending && <p role="status">Loading history…</p>}<ol className="history">{history.data?.map(event => <li key={event.id}><strong>{event.from_status ? `${label(event.from_status)} to ` : "Added · "}{label(event.to_status)}</strong><small>{new Date(event.created_at.endsWith("Z") || /[+-]\d\d:\d\d$/.test(event.created_at) ? event.created_at : event.created_at + "Z").toLocaleString("en-GB", { timeZone: "Europe/London" })} UK time</small></li>)}</ol></section><aside className="detail-aside"><section className="panel"><h3>Application status</h3><Field label="Update status"><select value={job.status} disabled={mutation.isPending} onChange={e => mutation.mutate(e.target.value as Status)}>{statuses.map(s => <option key={s} value={s}>{label(s)}</option>)}</select></Field><ErrorMessage error={mutation.error} /><p className="small muted">Preparation and submission statuses unlock in later phases.</p></section><section className="panel"><h3>Deadline</h3><Deadline value={job.deadline} /></section><section className="panel"><h3>Sponsorship</h3><span className="badge unverified">Unverified</span><p className="small muted">Check the role’s explicit sponsorship policy. A sponsor licence is a separate signal.</p><p className="small">Licensed sponsor: {job.licensed_sponsor === null ? "Not checked" : job.licensed_sponsor ? "Yes" : "No"}</p></section></aside></div></>;
}

function ProfileEditor({ profile }: { profile: Profile | undefined }) {
  const queryClient = useQueryClient();
  const facts = useQuery({ queryKey: ["facts"], queryFn: () => api<Fact[]>("facts") });
  return <div className="profile-grid"><section className="panel form-panel"><div className="panel-heading"><h2>Personal profile</h2><p className="muted small">No details are inferred or prefilled.</p></div>{profile ? <ProfileForm key={JSON.stringify(profile)} profile={profile} /> : <p role="status">Loading profile…</p>}<div className="notice">Fixed declarations below are entered and confirmed only by you.</div></section><section className="panel form-panel"><div className="panel-heading"><h2>Verified facts<span className="count-pill">{facts.data?.length ?? 0}</span></h2><p className="muted small">Facts keep their IDs when edited. Changed content requires a new review.</p></div><FactForm /><ErrorMessage error={facts.error} />{facts.isPending && <p role="status">Loading facts…</p>}<div className="fact-list">{facts.data?.map(fact => <FactCard key={fact.id} fact={fact} onChanged={() => queryClient.invalidateQueries({ queryKey: ["facts"] })} />)}{facts.data?.length === 0 && <p className="small muted">No facts saved. Add an education, experience, project, or skill fact above. Use CV upload above to extract more candidates.</p>}</div></section></div>;
}

function ProfileForm({ profile }: { profile: Profile }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState(profile);
  const mutation = useMutation({ mutationFn: () => api<Profile>("profile", "PUT", form), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile"] }) });
  const deletion = useMutation({ mutationFn: () => api("profile", "DELETE"), onSuccess: () => { setForm(blankProfile); return queryClient.invalidateQueries({ queryKey: ["profile"] }); } });
  function submit(event: FormEvent) { event.preventDefault(); mutation.mutate(); }
  return <form onSubmit={submit}><Field label="Display name"><input maxLength={200} value={form.display_name} onChange={e => setForm({ ...form, display_name: e.target.value })} autoComplete="name" /></Field><Field label="Email"><input type="email" maxLength={320} value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} autoComplete="email" /></Field><Field label="Graduation year"><input type="number" min={1900} max={2200} value={form.graduation_year ?? ""} onChange={e => setForm({ ...form, graduation_year: e.target.value ? Number(e.target.value) : null })} /></Field><Field label="Preferred locations"><input maxLength={500} value={form.target_locations} onChange={e => setForm({ ...form, target_locations: e.target.value })} /></Field><ErrorMessage error={mutation.error ?? deletion.error} /><div className="form-actions"><Button variant="ghost" disabled={deletion.isPending || mutation.isPending} onClick={() => { if (window.confirm("Clear your personal profile? Saved facts will be kept.")) deletion.mutate(); }}>Clear profile</Button><Button type="submit" disabled={mutation.isPending || deletion.isPending}>{mutation.isPending ? "Saving…" : "Save profile"}</Button></div></form>;
}

function FactForm({ fact, onDone }: { fact?: Fact; onDone?: () => void }) {
  const queryClient = useQueryClient();
  const [content, setContent] = useState(fact?.content ?? "");
  const [source, setSource] = useState(fact?.source ?? "");
  const [category, setCategory] = useState(fact?.category ?? "education");
  const mutation = useMutation({ mutationFn: () => api<Fact>(fact ? `facts/${fact.id}` : "facts", fact ? "PUT" : "POST", { content, source, category, verified: false }), onSuccess: async () => { setContent(""); setSource(""); await queryClient.invalidateQueries({ queryKey: ["facts"] }); onDone?.(); } });
  return <form className="fact-form" onSubmit={e => { e.preventDefault(); mutation.mutate(); }}><Field label="Fact category"><select value={category} onChange={e => setCategory(e.target.value)}>{["education", "experience", "project", "skill"].map(c => <option key={c} value={c}>{label(c)}</option>)}</select></Field><Field label="Fact"><textarea rows={3} required maxLength={10000} value={content} onChange={e => setContent(e.target.value)} placeholder="A specific statement you can verify" /></Field><Field label="Source"><input required maxLength={500} value={source} onChange={e => setSource(e.target.value)} placeholder="e.g. CV section or project record" /></Field><ErrorMessage error={mutation.error} /><div className="form-actions">{fact && <Button variant="ghost" onClick={onDone}>Cancel</Button>}<Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Saving…" : fact ? "Save for review" : "Add fact for review"}</Button></div></form>;
}

function FactCard({ fact, onChanged }: { fact: Fact; onChanged: () => Promise<unknown> }) {
  const [editing, setEditing] = useState(false);
  const mutation = useMutation({ mutationFn: () => api(`facts/${fact.id}`, "PUT", { category: fact.category, content: fact.content, source: fact.source, verified: !fact.verified }), onSuccess: onChanged });
  const deletion = useMutation({ mutationFn: () => api(`facts/${fact.id}`, "DELETE"), onSuccess: onChanged });
  return <article className="fact-card">{editing ? <FactForm fact={fact} onDone={() => setEditing(false)} /> : <><div className="fact-meta"><span>{label(fact.category)}</span><span className={`badge ${fact.verified ? "status-shortlisted" : "unverified"}`}>{fact.verified ? "Reviewed" : "Needs review"}</span></div><p className="preserve">{fact.content}</p><p className="small muted">Source: {fact.source}</p><code className="fact-id">{fact.id}</code><ErrorMessage error={mutation.error ?? deletion.error} /><div className="fact-actions"><Button variant="outline" disabled={mutation.isPending || deletion.isPending} onClick={() => mutation.mutate()}>{fact.verified ? "Mark unreviewed" : "I confirm this fact"}</Button><Button variant="ghost" onClick={() => setEditing(true)}>Edit</Button><Button variant="destructive" disabled={deletion.isPending || mutation.isPending} onClick={() => { if (window.confirm("Delete this fact?")) deletion.mutate(); }}>Delete</Button></div></>}</article>;
}
