/* BookStore UI logic: GIVEN CODE, you do not need to edit this file.
 *
 * How it works:
 *  - Every 3 seconds it downloads /openapi.json (which FastAPI generates from
 *    your code) and checks which endpoints exist.
 *  - Features whose endpoint is missing are shown as locked, with the
 *    checkpoint number that unlocks them.
 *  - Every request is shown in the request log at the bottom of the page.
 */

const GENRES = ["fiction", "fantasy", "science", "history", "programming", "children"];

// feature key -> endpoint + the checkpoint that builds it
const FEATURES = {
  welcome:     { method: "get",    path: "/api",                          cp: 0 },
  readBook:    { method: "get",    path: "/api/books/{book_id}",          cp: 1 },
  genre:       { method: "get",    path: "/api/genres/{genre}",           cp: 1 },
  listBooks:   { method: "get",    path: "/api/books",                    cp: 2 },
  createBook:  { method: "post",   path: "/api/books",                    cp: 3 },
  updateBook:  { method: "put",    path: "/api/books/{book_id}",          cp: 5 },
  addReview:   { method: "post",   path: "/api/books/{book_id}/reviews",  cp: 5 },
  listReviews: { method: "get",    path: "/api/books/{book_id}/reviews",  cp: 5 },
  createOrder: { method: "post",   path: "/api/orders",                   cp: 7 },
  readOrder:   { method: "get",    path: "/api/orders/{order_id}",        cp: 7 },
  recs:        { method: "get",    path: "/api/recommendations",          cp: 8 },
  clientInfo:  { method: "get",    path: "/api/client-info",              cp: 8 },
  register:    { method: "post",   path: "/api/users",                    cp: 10 },
  deleteBook:  { method: "delete", path: "/api/books/{book_id}",          cp: 11 },
  login:       { method: "post",   path: "/api/login",                    cp: 12 },
  bookRequest: { method: "post",   path: "/api/book-requests",            cp: 12 },
  uploadCover: { method: "post",   path: "/api/books/{book_id}/cover",    cp: 13 },
  withCover:   { method: "post",   path: "/api/books/with-cover",         cp: 13 },
  importCsv:   { method: "post",   path: "/api/books/import",             cp: 13 },
};

const CHECKPOINTS = [
  { title: "First steps", lessons: "Lesson 1", desc: "GET /api returns a welcome message. Then explore /docs.",
    check: () => has("welcome") },
  { title: "Path parameters", lessons: "Lesson 2", desc: "GET /api/books/{book_id} and GET /api/genres/{genre} with a Genre enum.",
    check: () => has("readBook") && has("genre") },
  { title: "Query parameters", lessons: "Lesson 3", desc: "GET /api/books with skip, limit, genre and in_stock.",
    check: () => ["skip", "limit", "genre", "in_stock"].every(p => param("listBooks", p, "query")) },
  { title: "Request body", lessons: "Lesson 4", desc: "BookCreate model and POST /api/books.",
    check: () => has("createBook") && !!op("createBook").requestBody },
  { title: "Query & Path validations", lessons: "Lessons 5–6", desc: "Search q (3–50 chars), repeated ?tag=, book_id ≥ 1, limit ≤ 50.",
    check: () => deepHas(param("listBooks", "q", "query"), "minLength", 3) && !!param("listBooks", "tag", "query")
      && deepHas(param("readBook", "book_id", "path"), "minimum", 1) },
  { title: "Multiple parameters", lessons: "Lesson 7", desc: "PUT a book (path + body + change_note + ?notify), reviews with Body(embed=True).",
    check: () => has("updateBook") && !!param("updateBook", "notify", "query")
      && deepHas(bodySchema("updateBook"), "change_note") && deepHas(bodySchema("addReview"), "review") && has("listReviews") },
  { title: "Body fields", lessons: "Lesson 8", desc: "Field() rules: price > 0, rating 1–5, title length.",
    check: () => schemaProp("BookCreate", "price", "exclusiveMinimum") === 0 && schemaProp("Review", "rating", "maximum") === 5 },
  { title: "Nested models & extra types", lessons: "Lessons 9–10", desc: "Orders with Customer, list[OrderItem], set of coupons, date; GET order by UUID.",
    check: () => has("createOrder") && has("readOrder") && !!schemaProp("OrderCreate", "items")
      && deepHas(param("readOrder", "order_id", "path"), "format", "uuid") },
  { title: "Cookies & headers", lessons: "Lessons 11–12", desc: "X-Currency header, preferred_genre cookie, GET /api/client-info.",
    check: () => !!param("listBooks", "x-currency", "header") && !!param("recs", "preferred_genre", "cookie") && has("clientInfo") },
  { title: "Parameter models", lessons: "Lessons 13–15", desc: "BookFilter query model (extra forbidden), Preferences cookie model, ClientHeaders header model.",
    check: () => probe.queryModel === true },
  { title: "Response models", lessons: "Lessons 16–17", desc: "Hide cost_price & supplier with BookOut; register users without echoing the password.",
    check: () => respRef("register") === "UserOut" && respRef("readBook") === "BookOut" && respRef("listBooks") === "BookList" },
  { title: "Status codes", lessons: "Lesson 18", desc: "201 for creates, 204 for DELETE /api/books/{book_id}.",
    check: () => !!op("createBook").responses?.["201"] && !!op("deleteBook").responses?.["204"] && !!op("createOrder").responses?.["201"] },
  { title: "Forms", lessons: "Lessons 19, 22", desc: "POST /api/login with Form(), and a BookRequestForm form model.",
    check: () => !!op("login").requestBody?.content?.["application/x-www-form-urlencoded"] && has("bookRequest") },
  { title: "Files", lessons: "Lessons 20–21", desc: "Upload covers (UploadFile), book + cover in one form, CSV import (bytes).",
    check: () => has("uploadCover") && has("withCover") && has("importCsv") },
];

// ---------------------------------------------------------------- state
const state = {
  spec: null, specText: "", doneCps: new Set(),
  view: "shop", page: 0, limit: 8, q: "", tags: new Set(), genre: "", inStock: false,
  currency: store("currency") || "BDT", cart: JSON.parse(store("cart") || "[]"),
  bookId: null, book: null, allTags: [], prevView: "shop", genreSel: "",
};
const probe = { queryModel: null, specText: "" };

function store(key, value) {
  try {
    if (value === undefined) return localStorage.getItem("bookstore." + key);
    localStorage.setItem("bookstore." + key, value);
  } catch { return null; }
}

// ---------------------------------------------------------------- helpers
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function op(feature) {
  const f = FEATURES[feature];
  return state.spec?.paths?.[f.path]?.[f.method] || {};
}
function has(feature) {
  const f = FEATURES[feature];
  return !!state.spec?.paths?.[f.path]?.[f.method];
}
function param(feature, name, where) {
  return (op(feature).parameters || []).find(p => p.name === name && (!where || p.in === where));
}
function resolve(schema) {
  if (schema && schema.$ref) {
    const name = schema.$ref.split("/").pop();
    return state.spec?.components?.schemas?.[name] || {};
  }
  return schema || {};
}
function bodySchema(feature) {
  const content = op(feature).requestBody?.content || {};
  const first = Object.values(content)[0];
  return resolve(first?.schema);
}
function schemaProp(model, prop, key) {
  const p = state.spec?.components?.schemas?.[model]?.properties?.[prop];
  if (!p) return undefined;
  return key ? p[key] : p;
}
function respRef(feature) {
  const responses = op(feature).responses || {};
  const ok = responses["200"] || responses["201"];
  const schema = ok?.content?.["application/json"]?.schema;
  return schema?.$ref?.split("/").pop();
}
// true if obj contains key (anywhere) and, if given, that key has value
function deepHas(obj, key, value) {
  if (!obj || typeof obj !== "object") return false;
  if (Object.prototype.hasOwnProperty.call(obj, key) && (value === undefined || obj[key] === value)) return true;
  if (obj.properties && Object.prototype.hasOwnProperty.call(obj.properties, key) && value === undefined) return true;
  return Object.values(obj).some(v => deepHas(v, key, value));
}

function toast(msg, kind = "") {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast show " + kind;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (t.className = "toast"), 2600);
}

function money(value, currency = "BDT") {
  const n = Number(value);
  if (Number.isNaN(n)) return esc(value);
  return currency === "USD" ? "$" + n.toFixed(2) : "৳" + n.toLocaleString("en-US", { maximumFractionDigits: 2 });
}
function stars(rating) {
  if (rating === null || rating === undefined) return '<span class="muted">No reviews yet</span>';
  const full = Math.round(Number(rating));
  return `<span class="stars">${"★".repeat(full)}${"☆".repeat(5 - full)}</span> <span class="muted">${Number(rating).toFixed(1)}</span>`;
}

// ---------------------------------------------------------------- API + request log
class ApiError extends Error {
  constructor(status, data) {
    super(typeof data?.detail === "string" ? data.detail : `HTTP ${status}`);
    this.status = status;
    this.data = data;
  }
}
const logEntries = [];

async function api(method, path, { query, json, form, multipart, headers = {}, quiet = false } = {}) {
  let url = path;
  if (query) {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries(query)) {
      if (v === undefined || v === null || v === "" || v === false && k !== "in_stock") continue;
      if (Array.isArray(v)) v.forEach(x => p.append(k, x));
      else p.append(k, v);
    }
    const s = p.toString();
    if (s) url += "?" + s;
  }
  const opts = { method, headers: { ...headers } };
  let sent = null;
  if (json !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(json);
    sent = JSON.stringify(json, null, 2);
  } else if (form) {
    opts.body = new URLSearchParams(form);
    sent = "form-urlencoded: " + opts.body.toString();
  } else if (multipart) {
    opts.body = multipart;
    sent = "multipart/form-data:\n" + [...multipart.entries()]
      .map(([k, v]) => `  ${k} = ${v instanceof File ? `<file ${v.name}, ${v.type || "?"}, ${v.size} bytes>` : v}`).join("\n");
  }
  const t0 = performance.now();
  let res, data = null;
  try {
    res = await fetch(url, opts);
    const text = await res.text();
    try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  } catch (e) {
    if (!quiet) addLog({ method, url, status: 0, ms: 0, headers: opts.headers, sent, data: String(e) });
    throw new ApiError(0, { detail: "The server is not reachable. Is `fastapi dev main.py` running?" });
  }
  if (!quiet) addLog({ method, url, status: res.status, ms: Math.round(performance.now() - t0), headers: opts.headers, sent, data });
  if (!res.ok) throw new ApiError(res.status, data);
  return { status: res.status, data };
}

function addLog(entry) {
  logEntries.unshift(entry);
  logEntries.length = Math.min(logEntries.length, 60);
  const cls = entry.status >= 500 || entry.status === 0 ? "s-err" : entry.status >= 400 ? "s-warn" : "s-ok";
  $("#log-last").innerHTML = `· <span class="m-${entry.method}">${entry.method}</span> ${esc(entry.url)} → <span class="${cls}">${entry.status || "failed"}</span>`;
  renderLog();
}
function renderLog() {
  $("#log-list").innerHTML = logEntries.map((e, i) => {
    const cls = e.status >= 500 || e.status === 0 ? "s-err" : e.status >= 400 ? "s-warn" : "s-ok";
    return `<div class="log-row" data-i="${i}"><span class="m-${e.method}">${e.method}</span><span>${esc(e.url)}</span>
      <span class="${cls}">${e.status || "ERR"}</span><span class="muted">${e.ms} ms</span></div>`;
  }).join("") || '<div class="log-row"><span></span><span class="muted">No requests yet</span></div>';
}
function showLogDetail(i) {
  const e = logEntries[i];
  if (!e) return;
  $$(".log-row").forEach(r => r.classList.toggle("sel", r.dataset.i === String(i)));
  const hdrs = Object.entries(e.headers || {}).map(([k, v]) => `  ${k}: ${v}`).join("\n");
  const body = e.data === null || e.data === "" ? "(empty body)" : typeof e.data === "string" ? e.data : JSON.stringify(e.data, null, 2);
  $("#log-detail").textContent =
    `${e.method} ${e.url}\n${hdrs ? "Headers:\n" + hdrs + "\n" : ""}${e.sent ? "Sent:\n" + e.sent + "\n" : ""}\n← ${e.status || "no response"} (${e.ms} ms)\n${body}`;
}

// show 422 validation errors next to the matching inputs
function showErrors(formEl, err) {
  if (!formEl) return;
  $$(".field-error.auto", formEl).forEach(n => n.remove());
  $$(".invalid", formEl).forEach(n => n.classList.remove("invalid"));
  const box = $(".form-error", formEl) || formEl.parentElement.querySelector(".form-error");
  if (box) box.textContent = "";
  if (!err) return;
  const detail = err.data?.detail;
  if (Array.isArray(detail)) {
    const leftovers = [];
    for (const d of detail) {
      const names = (d.loc || []).filter(x => typeof x === "string");
      const name = names[names.length - 1];
      const input = name && formEl.querySelector(`[name="${name}"]`);
      if (input) {
        input.classList.add("invalid");
        const msg = document.createElement("div");
        msg.className = "field-error auto";
        msg.textContent = d.msg;
        input.insertAdjacentElement("afterend", msg);
      } else {
        leftovers.push(`${(d.loc || []).join(" → ")}: ${d.msg}`);
      }
    }
    if (box && leftovers.length) box.textContent = leftovers.join(" · ");
    if (box && !leftovers.length) box.textContent = "";
  } else if (box) {
    box.textContent = err.status === 404 && detail === "Not Found"
      ? "This endpoint does not exist yet."
      : `${err.status ? err.status + ": " : ""}${detail || err.message}`;
  }
}

// ---------------------------------------------------------------- spec polling & locks
async function loadSpec() {
  let text = "";
  try {
    const res = await fetch("/openapi.json", { cache: "no-store" });
    text = res.ok ? await res.text() : "";
  } catch { text = ""; }
  const specChanged = text !== state.specText;
  if (specChanged) {
    state.specText = text;
    try { state.spec = text ? JSON.parse(text) : null; } catch { state.spec = null; }
  }
  const probeBefore = probe.queryModel;
  await runProbes();
  if (!specChanged && probe.queryModel === probeBefore) return;

  const before = new Set(state.doneCps);
  state.doneCps = new Set(CHECKPOINTS.map((c, i) => (safeCheck(c) ? i : null)).filter(i => i !== null));
  const newlyDone = [...state.doneCps].filter(i => !before.has(i));
  applyLocks();
  renderCheckpoints();
  if (state.loadedOnce && newlyDone.length) {
    toast(`🎉 Checkpoint ${newlyDone.join(", ")} complete: ${CHECKPOINTS[newlyDone[newlyDone.length - 1]].title}`, "good");
  }
  state.loadedOnce = true;
  renderView();
}
function safeCheck(c) { try { return !!c.check(); } catch { return false; } }

async function runProbes() {
  // CP9: a query-parameter model with extra="forbid" rejects unknown query params with 422.
  if (!has("listBooks")) { probe.queryModel = null; return; }
  try {
    await api("GET", "/api/books", { query: { limit: 1, checkpoint_probe: 1 }, quiet: true });
    probe.queryModel = false;
  } catch (e) {
    probe.queryModel = e.status === 422 && JSON.stringify(e.data || "").includes("extra_forbidden");
  }
}

function lockCard(feature) {
  const f = FEATURES[feature];
  const cp = CHECKPOINTS[f.cp];
  return `<div class="lock-overlay"><div class="lock-card">
    <div class="lk-title">🔒 Checkpoint ${f.cp} · ${esc(cp.title)}</div>
    <div>Build <code>${f.method.toUpperCase()} ${esc(f.path)}</code> in <code>main.py</code></div>
    <div class="lk-sub">Look for <code># TODO CP${f.cp}</code> · ${esc(cp.lessons)}</div></div></div>`;
}

function applyLocks() {
  const online = has("welcome");
  const pill = $("#api-status");
  pill.textContent = state.spec ? (online ? "API online" : "API running · CP0 to do") : "API offline";
  pill.className = "pill " + (online ? "pill-on" : "pill-off");

  $$(".lockable").forEach(el => {
    const feature = el.dataset.feature;
    const open = feature ? has(feature) : true;
    el.classList.toggle("locked", !open);
    const existing = el.querySelector(":scope > .lock-overlay");
    if (!open && !existing) el.insertAdjacentHTML("beforeend", lockCard(feature));
    if (open && existing) existing.remove();
  });
  $$("[data-cp]").forEach(el => {
    const cp = Number(el.dataset.cp);
    const open = state.doneCps.has(cp);
    el.classList.toggle("locked-inline", !open);
    el.dataset.lockLabel = `🔒 CP${cp}`;
  });
  $$("[data-feature-inline]").forEach(el => {
    const feature = el.dataset.featureInline;
    const open = has(feature);
    el.classList.toggle("locked-inline", !open);
    el.dataset.lockLabel = `🔒 CP${FEATURES[feature].cp}`;
  });
}

function renderCheckpoints() {
  $("#cp-count").textContent = `${state.doneCps.size}/${CHECKPOINTS.length}`;
  $("#cp-list").innerHTML = CHECKPOINTS.map((c, i) => `
    <li class="${state.doneCps.has(i) ? "done" : ""}">
      <span class="cp-dot">${state.doneCps.has(i) ? "✓" : i}</span>
      <div><div class="cp-title">CP${i} · ${esc(c.title)}</div>
        <div class="cp-desc">${esc(c.desc)}</div>
        <div class="cp-lessons">${esc(c.lessons)}</div></div>
    </li>`).join("");
}

// ---------------------------------------------------------------- rendering
function coverHtml(book) {
  const g = GENRES.includes(book.genre) ? book.genre : "other";
  const img = book.cover_url ? `<img src="${esc(book.cover_url)}" alt="">` : "";
  return `<div class="cover g-${g}">${img}<span class="c-genre">${esc(book.genre || "")}</span>
    <span><div class="c-title">${esc(book.title)}</div><div class="c-author">${esc(book.author)}</div></span></div>`;
}
function cardHtml(book) {
  return `<div class="card" data-book="${book.id}">${coverHtml(book)}
    <div class="card-body"><div class="card-title">${esc(book.title)}</div>
      <div class="card-author">${esc(book.author)}</div>
      <div class="card-foot"><span class="price">${money(book.price, book.currency)}</span>
        ${book.in_stock === false ? '<span class="badge badge-out">Out of stock</span>' : '<span class="badge">In stock</span>'}</div>
    </div></div>`;
}
function leakCheck(books, el) {
  const leaked = new Set();
  (Array.isArray(books) ? books : [books]).forEach(b => ["cost_price", "supplier"].forEach(k => b && k in b && leaked.add(k)));
  if (!el) return leaked;
  el.classList.toggle("hidden", !leaked.size);
  el.innerHTML = leaked.size
    ? `⚠ The API is exposing internal fields to customers: <b>${[...leaked].join(", ")}</b>. Hide them with a response model in Checkpoint 10.`
    : "";
  return leaked;
}

function setView(view) {
  if (view !== "book") state.prevView = view;
  state.view = view;
  $$(".view").forEach(v => v.classList.toggle("active", v.id === "view-" + view));
  $$("#nav button").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  window.scrollTo({ top: 0 });
  renderView();
}

function renderView() {
  const views = { shop: renderShop, genres: renderGenres, book: renderBook, cart: renderCart, account: () => {}, add: () => {}, request: () => {}, import: () => {} };
  (views[state.view] || (() => {}))();
  renderClientInfo();
}

// ---- shop
async function renderShop() {
  if (has("welcome")) {
    api("GET", "/api", { quiet: true }).then(r => { $("#welcome-msg").textContent = r.data?.message || "Welcome"; }).catch(() => {});
  }
  if (has("recs")) renderRecs();
  if (!has("listBooks")) return;
  if (state.doneCps.has(4) && !state.allTags.length) await loadTags();
  renderTagRow();

  const query = { skip: state.page * state.limit, limit: state.limit };
  if (state.genre) query.genre = state.genre;
  if (state.inStock) query.in_stock = true;
  if (state.doneCps.has(4)) {
    if (state.q) query.q = state.q;
    if (state.tags.size) query.tag = [...state.tags];
  }
  $("#search-error").textContent = "";
  $("#search").classList.remove("invalid");
  try {
    const { data } = await api("GET", "/api/books", { query, headers: { "X-Currency": state.currency } });
    const items = Array.isArray(data) ? data : data?.items || [];
    const total = Array.isArray(data) ? items.length : data?.total ?? items.length;
    $("#books").innerHTML = items.map(cardHtml).join("") || '<div class="empty">No books match these filters.</div>';
    $("#result-count").textContent = `${total} book${total === 1 ? "" : "s"}`;
    const from = total ? state.page * state.limit + 1 : 0;
    const to = Math.min(total, state.page * state.limit + items.length);
    $("#page-info").textContent = total ? `Showing ${from}–${to} of ${total}` : "";
    $("#prev").disabled = state.page === 0;
    $("#next").disabled = to >= total;
    leakCheck(items, $("#leak-banner"));
  } catch (e) {
    if (e.status === 422) {
      const d = Array.isArray(e.data?.detail) ? e.data.detail : [];
      const qErr = d.find(x => (x.loc || []).includes("q"));
      if (qErr) { $("#search-error").textContent = qErr.msg; $("#search").classList.add("invalid"); }
      $("#books").innerHTML = `<div class="empty">The server rejected the query (422). ${esc(d.map(x => `${(x.loc || []).join(".")}: ${x.msg}`).join(" · "))}</div>`;
    } else {
      $("#books").innerHTML = `<div class="empty">${esc(e.message)}</div>`;
    }
  }
}
async function loadTags() {
  try {
    const { data } = await api("GET", "/api/books", { query: { limit: 50 }, quiet: true });
    const items = Array.isArray(data) ? data : data?.items || [];
    state.allTags = [...new Set(items.flatMap(b => b.tags || []))].sort();
  } catch { state.allTags = []; }
}
function renderTagRow() {
  const tags = state.allTags.length ? state.allTags : ["python", "classic", "beginner", "magic"];
  $("#tag-row").innerHTML = '<span class="muted" style="font-size:13px">Tags (all must match):</span>' +
    tags.map(t => `<button class="tag ${state.tags.has(t) ? "on" : ""}" data-tag="${esc(t)}">${esc(t)}</button>`).join("");
}
async function renderRecs() {
  try {
    const { data } = await api("GET", "/api/recommendations", { quiet: true });
    const items = Array.isArray(data) ? data : data?.books || data?.items || [];
    $("#recs").innerHTML = items.map(cardHtml).join("") || '<div class="empty">No recommendations.</div>';
  } catch (e) {
    $("#recs").innerHTML = `<div class="empty">${esc(e.message)}</div>`;
  }
}

// ---- genres
async function renderGenres() {
  $("#genre-chips").innerHTML = GENRES.map(g => `<button class="chip ${state.genreSel === g ? "on" : ""}" data-genre="${g}">${g}</button>`).join("")
    + `<button class="chip" data-genre="cooking" title="Not a valid genre: watch the 422">cooking?</button>`;
  if (!has("genre") || !state.genreSel) {
    if (has("genre")) $("#genre-books").innerHTML = '<div class="empty">Pick a genre.</div>';
    return;
  }
  try {
    const { data } = await api("GET", `/api/genres/${encodeURIComponent(state.genreSel)}`);
    const items = Array.isArray(data) ? data : data?.books || [];
    $("#genre-books").innerHTML = items.map(cardHtml).join("") || '<div class="empty">No books in this genre.</div>';
  } catch (e) {
    const d = Array.isArray(e.data?.detail) ? e.data.detail.map(x => x.msg).join(" · ") : e.message;
    $("#genre-books").innerHTML = `<div class="empty">${e.status}: ${esc(d)}</div>`;
  }
}

// ---- book detail
function openBook(id) {
  state.bookId = Number(id);
  setView("book");
}
async function renderBook() {
  if (!state.bookId) return;
  const detail = $("#book-detail");
  if (!has("readBook")) { detail.innerHTML = ""; return; }
  try {
    const { data: book } = await api("GET", `/api/books/${state.bookId}`, { headers: { "X-Currency": state.currency } });
    state.book = book;
    leakCheck(book, $("#book-leak"));
    detail.innerHTML = `${coverHtml(book)}
      <div><p class="eyebrow">${esc(book.genre)} · Book #${book.id}</p>
        <h1>${esc(book.title)}</h1><div class="muted">by ${esc(book.author)}</div>
        <div class="meta"><span class="big-price">${money(book.price, book.currency)}</span>
          ${book.in_stock === false ? '<span class="badge badge-out">Out of stock</span>' : '<span class="badge">In stock</span>'}
          <span>${stars(book.rating)}</span></div>
        <p>${esc(book.description || "")}</p>
        <div class="tags">${(book.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("")}</div>
        <button class="btn" id="add-to-cart" ${book.in_stock === false ? "disabled" : ""}>Add to cart</button>
      </div>`;
    fillEditForm(book);
  } catch (e) {
    detail.innerHTML = `<div class="empty">${e.status}: ${esc(e.message)}</div>`;
    state.book = null;
  }
  if (has("listReviews")) renderReviews();
}
function fillEditForm(book) {
  const f = $("#edit-form");
  f.title.value = book.title || "";
  f.author.value = book.author || "";
  f.genre.value = book.genre || "fiction";
  f.price.value = book.currency === "USD" ? "" : book.price;
  f.price.placeholder = book.currency === "USD" ? "Switch currency to BDT to edit the price" : "";
  f.description.value = book.description || "";
  f.tags.value = (book.tags || []).join(", ");
  f.in_stock.checked = book.in_stock !== false;
  showErrors(f, null);
}
async function renderReviews() {
  try {
    const { data } = await api("GET", `/api/books/${state.bookId}/reviews`, { quiet: true });
    const items = Array.isArray(data) ? data : [];
    $("#reviews").innerHTML = items.length
      ? items.map(r => `<div class="review"><b>${esc(r.user)}</b>${stars(r.rating)}<div>${esc(r.comment || "")}</div></div>`).join("")
      : '<div class="muted">No reviews yet. Be the first!</div>';
  } catch (e) {
    $("#reviews").innerHTML = `<div class="muted">${esc(e.message)}</div>`;
  }
}

// ---- cart
function saveCart() {
  store("cart", JSON.stringify(state.cart));
  $("#cart-count").textContent = state.cart.reduce((n, l) => n + l.quantity, 0);
}
function addToCart(book) {
  const line = state.cart.find(l => l.book_id === book.id);
  if (line) line.quantity = Math.min(10, line.quantity + 1);
  else state.cart.push({ book_id: book.id, title: book.title, quantity: 1 });
  saveCart();
  toast(`Added “${book.title}” to your cart`, "good");
}
function renderCart() {
  const el = $("#cart-items");
  if (!state.cart.length) { el.innerHTML = '<div class="empty">Your cart is empty. Open a book and add it.</div>'; return; }
  el.innerHTML = state.cart.map((l, i) => `
    <div class="cart-line"><span><b>${esc(l.title)}</b> <span class="muted">#${l.book_id}</span></span>
      <span class="qty"><button class="btn btn-ghost btn-small" data-qty="${i}" data-d="-1">−</button>${l.quantity}
        <button class="btn btn-ghost btn-small" data-qty="${i}" data-d="1">+</button></span>
      <button class="btn btn-ghost btn-small" data-remove="${i}">Remove</button><span></span></div>`).join("");
}
function receiptHtml(o, title = "Order placed") {
  const items = (o.items || []).map(i => `<tr><td>${esc(i.title || "#" + i.book_id)}</td><td>${i.quantity}</td>
      <td>${i.unit_price !== undefined ? money(i.unit_price) : ""}</td><td>${i.line_total !== undefined ? money(i.line_total) : ""}</td></tr>`).join("");
  return `<div class="result"><h3>✓ ${esc(title)}</h3>
    <dl class="kv"><dt>Order ID (UUID)</dt><dd>${esc(o.order_id)}</dd>
      <dt>Created at (datetime)</dt><dd>${esc(o.created_at)}</dd>
      <dt>Customer</dt><dd>${esc(o.customer?.name)} · ${esc(o.customer?.email)}</dd>
      <dt>Coupons (set)</dt><dd>${esc((o.coupons || []).join(", ") || "none")}</dd>
      <dt>Deliver by (date)</dt><dd>${esc(o.deliver_by || "no date given")}</dd></dl>
    <table><tr><th>Book</th><th>Qty</th><th>Unit</th><th>Total</th></tr>${items}</table>
    <dl class="kv" style="margin-top:8px"><dt>Subtotal</dt><dd>${money(o.subtotal)}</dd><dt>Discount</dt><dd>${money(o.discount)}</dd>
      <dt>Total (Decimal)</dt><dd><b>${money(o.total)}</b></dd></dl></div>`;
}

// ---- client info (footer)
async function renderClientInfo() {
  if (!has("clientInfo")) { $("#client-info").textContent = ""; return; }
  if (renderClientInfo.busy) return;
  renderClientInfo.busy = true;
  try {
    const { data } = await api("GET", "/api/client-info", { headers: { "X-Currency": state.currency }, quiet: true });
    const ua = String(data?.user_agent || "unknown").replace(/^Mozilla\/5\.0 \(([^)]*)\).*$/, "$1");
    $("#client-info").textContent = `Server sees → browser: ${ua.slice(0, 48)} · language: ${data?.accept_language?.split(",")[0] || "?"} · currency: ${data?.x_currency || "?"}`;
  } catch { $("#client-info").textContent = ""; }
  renderClientInfo.busy = false;
}

// ---------------------------------------------------------------- form handlers
function formToBook(f) {
  const tags = f.tags.value.split(",").map(t => t.trim().toLowerCase()).filter(Boolean);
  return {
    title: f.title.value.trim(), author: f.author.value.trim(), genre: f.genre.value,
    price: f.price.value === "" ? null : Number(f.price.value), in_stock: f.in_stock.checked,
    description: f.description.value.trim() || null, tags,
  };
}

function bindEvents() {
  $("#nav").addEventListener("click", e => { const b = e.target.closest("button[data-view]"); if (b) setView(b.dataset.view); });
  $("[data-back]").addEventListener("click", () => setView(state.prevView || "shop"));
  $("#cp-toggle").addEventListener("click", () => $("#cp-panel").classList.toggle("open"));
  $("#cp-close").addEventListener("click", () => $("#cp-panel").classList.remove("open"));
  $("#log-toggle").addEventListener("click", () => $("#log").classList.toggle("open"));
  $("#log-list").addEventListener("click", e => { const r = e.target.closest(".log-row[data-i]"); if (r) showLogDetail(Number(r.dataset.i)); });

  document.addEventListener("click", e => {
    const card = e.target.closest(".card[data-book]");
    if (card && has("readBook")) openBook(card.dataset.book);
    else if (card) toast("Book details unlock at Checkpoint 1", "bad");
  });

  $("#currency").value = state.currency;
  $("#currency").addEventListener("change", e => { state.currency = e.target.value; store("currency", state.currency); renderView(); });

  // favourite genre -> cookie
  $("#fav-genre").innerHTML += GENRES.map(g => `<option value="${g}">${g}</option>`).join("");
  const fav = (document.cookie.match(/(?:^|; )preferred_genre=([^;]*)/) || [])[1] || "";
  $("#fav-genre").value = fav;
  $("#fav-genre").addEventListener("change", e => {
    document.cookie = e.target.value
      ? `preferred_genre=${e.target.value}; path=/; max-age=31536000; SameSite=Lax`
      : "preferred_genre=; path=/; max-age=0";
    renderRecs();
  });

  // shop filters
  $("#filter-genre").innerHTML += GENRES.map(g => `<option value="${g}">${g}</option>`).join("");
  $("#filter-genre").addEventListener("change", e => { state.genre = e.target.value; state.page = 0; renderShop(); });
  $("#filter-stock").addEventListener("change", e => { state.inStock = e.target.checked; state.page = 0; renderShop(); });
  let searchTimer;
  $("#search").addEventListener("input", e => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { state.q = e.target.value.trim(); state.page = 0; renderShop(); }, 450);
  });
  $("#tag-row").addEventListener("click", e => {
    const t = e.target.closest("[data-tag]");
    if (!t) return;
    state.tags.has(t.dataset.tag) ? state.tags.delete(t.dataset.tag) : state.tags.add(t.dataset.tag);
    state.page = 0;
    renderShop();
  });
  $("#prev").addEventListener("click", () => { state.page = Math.max(0, state.page - 1); renderShop(); });
  $("#next").addEventListener("click", () => { state.page += 1; renderShop(); });

  // genres
  $("#genre-chips").addEventListener("click", e => { const c = e.target.closest("[data-genre]"); if (c) { state.genreSel = c.dataset.genre; renderGenres(); } });
  $("#open-book").addEventListener("submit", async e => {
    e.preventDefault();
    const f = e.target;
    showErrors(f, null);
    try {
      await api("GET", `/api/books/${encodeURIComponent(f.book_id.value)}`, { headers: { "X-Currency": state.currency } });
      openBook(f.book_id.value);
    } catch (err) { showErrors(f, err); }
  });
  $$(".genre-select").forEach(s => (s.innerHTML = GENRES.map(g => `<option value="${g}">${g}</option>`).join("")));

  // book detail
  document.addEventListener("click", e => { if (e.target.id === "add-to-cart" && state.book) addToCart(state.book); });
  $("#review-form").addEventListener("submit", async e => {
    e.preventDefault();
    const f = e.target;
    showErrors(f, null);
    const review = { user: f.user.value.trim(), rating: Number(f.rating.value), comment: f.comment.value.trim() || null };
    try {
      await api("POST", `/api/books/${state.bookId}/reviews`, { json: { review } });
      f.reset();
      toast("Review posted", "good");
      renderBook();
    } catch (err) { showErrors(f, err); }
  });
  $("#edit-form").addEventListener("submit", async e => {
    e.preventDefault();
    const f = e.target;
    showErrors(f, null);
    const body = { book: formToBook(f), change_note: f.change_note.value.trim() };
    try {
      await api("PUT", `/api/books/${state.bookId}`, { query: { notify: f.notify.checked }, json: body });
      toast(f.notify.checked ? "Saved · subscribers notified" : "Saved", "good");
      f.change_note.value = "";
      renderBook();
    } catch (err) { showErrors(f, err); }
  });
  $("#cover-form").addEventListener("submit", async e => {
    e.preventDefault();
    const f = e.target;
    showErrors(f, null);
    if (!f.file.files[0]) { $(".form-error", f.parentElement).textContent = "Choose an image first."; return; }
    const fd = new FormData();
    fd.append("file", f.file.files[0]);
    try {
      await api("POST", `/api/books/${state.bookId}/cover`, { multipart: fd });
      f.reset();
      toast("Cover uploaded", "good");
      renderBook();
    } catch (err) { showErrors(f, err); }
  });
  $("#delete-book").addEventListener("click", async () => {
    if (!state.book || !confirm(`Delete “${state.book.title}”?`)) return;
    try {
      const r = await api("DELETE", `/api/books/${state.bookId}`);
      toast(`Deleted (status ${r.status})`, "good");
      state.cart = state.cart.filter(l => l.book_id !== state.bookId);
      saveCart();
      setView("shop");
    } catch (err) { toast(err.message, "bad"); }
  });

  // add book
  const addForm = $("#add-form");
  addForm.with_cover.addEventListener("change", e => addForm.cover.classList.toggle("hidden", !e.target.checked));
  addForm.addEventListener("submit", async e => {
    e.preventDefault();
    showErrors(addForm, null);
    $("#add-result").innerHTML = "";
    try {
      let res;
      if (addForm.with_cover.checked) {
        const fd = new FormData();
        ["title", "author", "genre", "price"].forEach(k => fd.append(k, addForm[k].value));
        if (addForm.cover.files[0]) fd.append("cover", addForm.cover.files[0]);
        res = await api("POST", "/api/books/with-cover", { multipart: fd });
      } else {
        res = await api("POST", "/api/books", { json: formToBook(addForm) });
      }
      const b = res.data || {};
      const leaked = leakCheck(b);
      $("#add-result").innerHTML = `<div class="result"><h3>✓ Created (status ${res.status})</h3>
        <dl class="kv"><dt>id</dt><dd>${esc(b.id)}</dd><dt>title</dt><dd>${esc(b.title)}</dd><dt>tags</dt><dd>${esc(JSON.stringify(b.tags))}</dd>
        <dt>cover</dt><dd>${esc(b.cover_url || "none")}</dd></dl>
        ${leaked.size ? `<p class="banner banner-warn">⚠ Response exposes ${[...leaked].join(", ")} (fix in Checkpoint 10)</p>` : ""}
        ${b.id ? `<button class="btn btn-small" onclick="openBook(${Number(b.id)})">Open book</button>` : ""}</div>`;
      state.allTags = [];
      addForm.reset();
      addForm.cover.classList.add("hidden");
    } catch (err) { showErrors(addForm, err); }
  });

  // cart
  $("#cart-items").addEventListener("click", e => {
    const q = e.target.closest("[data-qty]");
    const r = e.target.closest("[data-remove]");
    if (q) {
      const line = state.cart[Number(q.dataset.qty)];
      line.quantity = Math.max(1, Math.min(10, line.quantity + Number(q.dataset.d)));
    }
    if (r) state.cart.splice(Number(r.dataset.remove), 1);
    saveCart();
    renderCart();
  });
  $("#checkout-form").addEventListener("submit", async e => {
    e.preventDefault();
    const f = e.target;
    showErrors(f, null);
    $("#receipt").innerHTML = "";
    const order = {
      customer: { name: f.name.value.trim(), email: f.email.value.trim(), phone: f.phone.value.trim() || null },
      items: state.cart.map(l => ({ book_id: l.book_id, quantity: l.quantity })),
      coupons: f.coupons.value.split(",").map(c => c.trim()).filter(Boolean),
      deliver_by: f.deliver_by.value || null,
    };
    try {
      const { data } = await api("POST", "/api/orders", { json: order });
      $("#receipt").innerHTML = receiptHtml(data);
      $("#track-form").order_id.value = data.order_id || "";
      state.cart = [];
      saveCart();
      renderCart();
    } catch (err) { showErrors(f, err); }
  });
  $("#track-form").addEventListener("submit", async e => {
    e.preventDefault();
    const f = e.target;
    showErrors(f, null);
    $("#track-result").innerHTML = "";
    try {
      const { data } = await api("GET", `/api/orders/${encodeURIComponent(f.order_id.value.trim())}`);
      $("#track-result").innerHTML = receiptHtml(data, `Order status: ${data.status || "?"}`);
    } catch (err) { showErrors(f, err); }
  });

  // account
  $("#register-form").addEventListener("submit", async e => {
    e.preventDefault();
    const f = e.target;
    showErrors(f, null);
    $("#register-result").innerHTML = "";
    const user = { username: f.username.value.trim(), email: f.email.value.trim(), full_name: f.full_name.value.trim() || null, password: f.password.value };
    try {
      const { data, status } = await api("POST", "/api/users", { json: user });
      const leak = ["password", "hashed_password"].filter(k => data && k in data);
      $("#register-result").innerHTML = `<div class="result"><h3>✓ Account created (status ${status})</h3>
        <pre style="margin:0;white-space:pre-wrap">${esc(JSON.stringify(data, null, 2))}</pre>
        ${leak.length ? `<p class="banner banner-warn">⚠ The response contains <b>${leak.join(", ")}</b>! Use response_model=UserOut.</p>` : ""}</div>`;
      f.reset();
    } catch (err) { showErrors(f, err); }
  });
  $("#login-form").addEventListener("submit", async e => {
    e.preventDefault();
    const f = e.target;
    showErrors(f, null);
    $("#login-result").innerHTML = "";
    try {
      const { data } = await api("POST", "/api/login", { form: { username: f.username.value, password: f.password.value } });
      $("#login-result").innerHTML = `<div class="result"><h3>✓ ${esc(data?.message || "Logged in")}</h3></div>`;
    } catch (err) { showErrors(f, err); }
  });

  // request a book (form model)
  $("#request-form").addEventListener("submit", async e => {
    e.preventDefault();
    const f = e.target;
    showErrors(f, null);
    $("#request-result").innerHTML = "";
    const form = {};
    ["title", "author", "email", "note"].forEach(k => { if (f[k].value.trim()) form[k] = f[k].value.trim(); });
    try {
      const { data, status } = await api("POST", "/api/book-requests", { form });
      $("#request-result").innerHTML = `<div class="result"><h3>✓ Request #${esc(data?.id)} received (status ${status})</h3>
        <dl class="kv"><dt>title</dt><dd>${esc(data?.title)}</dd><dt>status</dt><dd>${esc(data?.status)}</dd></dl></div>`;
      f.reset();
    } catch (err) { showErrors(f, err); }
  });

  // CSV import (bytes)
  $("#import-form").addEventListener("submit", async e => {
    e.preventDefault();
    const f = e.target;
    showErrors(f, null);
    $("#import-result").innerHTML = "";
    if (!f.file.files[0]) { $(".form-error", f.parentElement).textContent = "Choose a CSV file first."; return; }
    const fd = new FormData();
    fd.append("file", f.file.files[0]);
    try {
      const { data, status } = await api("POST", "/api/books/import", { multipart: fd });
      $("#import-result").innerHTML = `<div class="result"><h3>✓ Imported ${esc(data?.imported)} book(s) (status ${status})</h3>
        <div>${esc((data?.titles || []).join(", "))}</div>
        ${data?.skipped_lines?.length ? `<div class="muted">Skipped invalid lines: ${esc(data.skipped_lines.join(", "))}</div>` : ""}</div>`;
      state.allTags = [];
      f.reset();
    } catch (err) { showErrors(f, err); }
  });
}

// ---------------------------------------------------------------- start
bindEvents();
saveCart();
renderLog();
renderCheckpoints();
applyLocks();
loadSpec();
setInterval(() => { if (!document.hidden) loadSpec(); }, 3000);
window.openBook = openBook;
