<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  MessageSquareIcon,
  ScrollTextIcon,
  DatabaseIcon,
  BookOpenIcon,
  CheckIcon,
  XIcon,
  PencilIcon,
  Trash2Icon,
  PlusIcon,
  SearchIcon,
  UploadIcon,
  LogOutIcon,
  ChevronDownIcon,
  RefreshCwIcon,
} from 'lucide-vue-next'

const apiBase = import.meta.env.VITE_API_BASE_URL || ''

// ── Auth ─────────────────────────────────────────────────────────────────────
const adminKey = ref(sessionStorage.getItem('adminKey') || '')
const keyInput = ref('')
const authError = ref('')
const isAuthenticated = ref(!!adminKey.value)

async function login() {
  authError.value = ''
  const res = await fetch(`${apiBase}/api/admin/comments/pending`, {
    headers: { 'X-Admin-Key': keyInput.value },
  })
  if (res.ok) {
    adminKey.value = keyInput.value
    sessionStorage.setItem('adminKey', keyInput.value)
    isAuthenticated.value = true
    loadAll()
  } else {
    authError.value = 'Invalid key.'
  }
}

function logout() {
  sessionStorage.removeItem('adminKey')
  adminKey.value = ''
  isAuthenticated.value = false
  keyInput.value = ''
}

const headers = computed(() => ({
  'Content-Type': 'application/json',
  'X-Admin-Key': adminKey.value,
}))

// ── Tab ───────────────────────────────────────────────────────────────────────
const activeTab = ref('comments')

// ── Toast ─────────────────────────────────────────────────────────────────────
const toast = ref(null)
let toastTimer = null
function showToast(msg, type = 'ok') {
  clearTimeout(toastTimer)
  toast.value = { msg, type }
  toastTimer = setTimeout(() => { toast.value = null }, 3500)
}

// ── Comments ──────────────────────────────────────────────────────────────────
const pendingComments = ref([])
const commentsLoading = ref(false)

async function loadComments() {
  commentsLoading.value = true
  try {
    const res = await fetch(`${apiBase}/api/admin/comments/pending`, { headers: headers.value })
    if (res.ok) pendingComments.value = await res.json()
  } finally {
    commentsLoading.value = false
  }
}

async function moderateComment(id, approved) {
  const res = await fetch(`${apiBase}/api/admin/comments/${id}`, {
    method: 'PATCH',
    headers: headers.value,
    body: JSON.stringify({ approved }),
  })
  if (res.ok) {
    pendingComments.value = pendingComments.value.filter((c) => c.id !== id)
    showToast(approved ? 'Comment approved.' : 'Comment rejected.')
  }
}

// ── Poems ─────────────────────────────────────────────────────────────────────
const allPoems = ref([])
const poemsLoading = ref(false)
const showCreateForm = ref(false)
const editingPoemId = ref(null)

const createForm = ref({ title: '', body: '', excerpt: '', tags: '' })
const editForm = ref({ title: '', body: '', excerpt: '', tags: '' })

async function loadPoems() {
  poemsLoading.value = true
  try {
    const res = await fetch(`${apiBase}/api/gallery/poems`)
    if (res.ok) allPoems.value = await res.json()
  } finally {
    poemsLoading.value = false
  }
}

async function createPoem() {
  const res = await fetch(`${apiBase}/api/gallery/poems`, {
    method: 'POST',
    headers: headers.value,
    body: JSON.stringify({
      title: createForm.value.title,
      body: createForm.value.body,
      excerpt: createForm.value.excerpt || undefined,
      tags: createForm.value.tags.split(',').map((t) => t.trim()).filter(Boolean),
    }),
  })
  if (res.ok) {
    createForm.value = { title: '', body: '', excerpt: '', tags: '' }
    showCreateForm.value = false
    await loadPoems()
    showToast('Poem created.')
  } else {
    showToast('Failed to create poem.', 'err')
  }
}

function startEdit(poem) {
  editingPoemId.value = poem.id
  editForm.value = {
    title: poem.title,
    body: poem.body,
    excerpt: poem.excerpt || '',
    tags: poem.tags.join(', '),
  }
}

function cancelEdit() {
  editingPoemId.value = null
}

async function saveEdit(poem) {
  const res = await fetch(`${apiBase}/api/gallery/poems/${poem.id}`, {
    method: 'PATCH',
    headers: headers.value,
    body: JSON.stringify({
      title: editForm.value.title,
      body: editForm.value.body,
      excerpt: editForm.value.excerpt || undefined,
      tags: editForm.value.tags.split(',').map((t) => t.trim()).filter(Boolean),
    }),
  })
  if (res.ok) {
    editingPoemId.value = null
    await loadPoems()
    showToast('Poem updated.')
  } else {
    showToast('Failed to update poem.', 'err')
  }
}

async function deletePoem(poem) {
  if (!confirm(`Delete "${poem.title}"? This can't be undone.`)) return
  const res = await fetch(`${apiBase}/api/gallery/poems/${poem.id}`, {
    method: 'DELETE',
    headers: headers.value,
  })
  if (res.status === 204 || res.ok) {
    allPoems.value = allPoems.value.filter((p) => p.id !== poem.id)
    showToast('Poem deleted.')
  } else {
    showToast('Failed to delete poem.', 'err')
  }
}

function loadMdFile(target, formRef) {
  const file = target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target.result
    formRef.body = text
    // Extract # Title from first line if present
    const firstLine = text.split('\n')[0] || ''
    if (firstLine.startsWith('# ') && !formRef.title) {
      formRef.title = firstLine.slice(2).trim()
      formRef.body = text.replace(firstLine, '').trimStart()
    }
  }
  reader.readAsText(file)
  target.value = ''
}

const poemTitleMap = computed(() =>
  Object.fromEntries(allPoems.value.map((p) => [p.id, p.title]))
)

// ── Reading ───────────────────────────────────────────────────────────────────
const readingData = ref({ current: null, recent: [] })
const readingLoading = ref(false)

const currentForm = ref({ title: '', author: '', thoughts: '', progress: 0, since: '', cover: '' })
const recentForm = ref({ title: '', author: '', finished_at: '' })
const savingCurrent = ref(false)
const addingRecent = ref(false)
const clearingCache = ref(false)

async function loadReading() {
  readingLoading.value = true
  try {
    const res = await fetch(`${apiBase}/api/reading`)
    if (res.ok) {
      readingData.value = await res.json()
      const c = readingData.value.current
      if (c) {
        currentForm.value = {
          title: c.title || '',
          author: c.author || '',
          thoughts: c.thoughts || '',
          progress: c.progress ?? 0,
          since: c.since || '',
          cover: c.cover || '',
        }
      }
    }
  } finally {
    readingLoading.value = false
  }
}

async function saveCurrentBook() {
  savingCurrent.value = true
  try {
    const res = await fetch(`${apiBase}/api/admin/reading/current`, {
      method: 'PUT',
      headers: headers.value,
      body: JSON.stringify({
        title: currentForm.value.title,
        author: currentForm.value.author,
        thoughts: currentForm.value.thoughts,
        progress: Number(currentForm.value.progress),
        since: currentForm.value.since,
        cover: currentForm.value.cover || null,
      }),
    })
    if (res.ok) {
      readingData.value.current = await res.json()
      showToast('Reading updated.')
    } else {
      showToast('Failed to save.', 'err')
    }
  } finally {
    savingCurrent.value = false
  }
}

async function addRecentBook() {
  if (!recentForm.value.title || !recentForm.value.author) return
  addingRecent.value = true
  try {
    const res = await fetch(`${apiBase}/api/admin/reading/recent`, {
      method: 'POST',
      headers: headers.value,
      body: JSON.stringify({
        title: recentForm.value.title,
        author: recentForm.value.author,
        finished_at: recentForm.value.finished_at || null,
      }),
    })
    if (res.ok) {
      const book = await res.json()
      readingData.value.recent.push(book)
      recentForm.value = { title: '', author: '', finished_at: '' }
      showToast('Book added.')
    } else {
      showToast('Failed to add.', 'err')
    }
  } finally {
    addingRecent.value = false
  }
}

async function deleteRecentBook(id) {
  const res = await fetch(`${apiBase}/api/admin/reading/recent/${id}`, {
    method: 'DELETE',
    headers: headers.value,
  })
  if (res.status === 204 || res.ok) {
    readingData.value.recent = readingData.value.recent.filter((b) => b.id !== id)
    showToast('Removed.')
  } else {
    showToast('Failed to remove.', 'err')
  }
}

async function clearResumeCache() {
  clearingCache.value = true
  try {
    const res = await fetch(`${apiBase}/api/admin/resume/cache`, {
      method: 'DELETE',
      headers: headers.value,
    })
    if (res.ok) {
      showToast('Resume cache cleared — next visit will re-parse.')
    } else {
      showToast('Failed to clear cache.', 'err')
    }
  } finally {
    clearingCache.value = false
  }
}

// ── Pinecone ──────────────────────────────────────────────────────────────────
const pineconeIndexes = ref({})
const pineconeLoading = ref(false)

const pcIndex = ref('')
const pcNamespace = ref('')
const pcSearchQuery = ref('')
const pcSearchResults = ref([])
const pcSearching = ref(false)

const pcAddText = ref('')
const pcAddId = ref('')
const pcAdding = ref(false)

async function loadPineconeIndexes() {
  pineconeLoading.value = true
  try {
    const res = await fetch(`${apiBase}/api/admin/pinecone/indexes`, { headers: headers.value })
    if (res.ok) {
      pineconeIndexes.value = await res.json()
      const names = Object.keys(pineconeIndexes.value)
      if (names.length && !pcIndex.value) pcIndex.value = names[0]
    }
  } finally {
    pineconeLoading.value = false
  }
}

async function searchRecords() {
  if (!pcSearchQuery.value.trim()) return
  pcSearching.value = true
  pcSearchResults.value = []
  try {
    const res = await fetch(`${apiBase}/api/admin/pinecone/search`, {
      method: 'POST',
      headers: headers.value,
      body: JSON.stringify({
        index_name: pcIndex.value,
        namespace: pcNamespace.value,
        query: pcSearchQuery.value,
        top_k: 10,
      }),
    })
    if (res.ok) {
      const data = await res.json()
      pcSearchResults.value = data.hits || []
    } else {
      showToast('Search failed.', 'err')
    }
  } finally {
    pcSearching.value = false
  }
}

async function addRecord() {
  if (!pcAddText.value.trim()) return
  pcAdding.value = true
  try {
    const res = await fetch(`${apiBase}/api/admin/pinecone/records`, {
      method: 'POST',
      headers: headers.value,
      body: JSON.stringify({
        index_name: pcIndex.value,
        namespace: pcNamespace.value,
        text: pcAddText.value,
        record_id: pcAddId.value || undefined,
      }),
    })
    if (res.ok) {
      const data = await res.json()
      showToast(`Upserted: ${data.id}`)
      pcAddText.value = ''
      pcAddId.value = ''
    } else {
      showToast('Upsert failed.', 'err')
    }
  } finally {
    pcAdding.value = false
  }
}

async function deleteRecord(id) {
  const res = await fetch(`${apiBase}/api/admin/pinecone/records`, {
    method: 'DELETE',
    headers: headers.value,
    body: JSON.stringify({
      index_name: pcIndex.value,
      namespace: pcNamespace.value,
      ids: [id],
    }),
  })
  if (res.ok) {
    pcSearchResults.value = pcSearchResults.value.filter((h) => h.id !== id)
    showToast('Record deleted.')
  } else {
    showToast('Delete failed.', 'err')
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
function loadAll() {
  loadComments()
  loadPoems()
  loadPineconeIndexes()
  loadReading()
}

onMounted(() => { if (isAuthenticated.value) loadAll() })
</script>

<template>
  <!-- ── Login ── -->
  <div v-if="!isAuthenticated" class="login-wrap">
    <div class="login-box">
      <p class="login-label">// admin</p>
      <form class="login-form" @submit.prevent="login">
        <input
          v-model="keyInput"
          type="password"
          class="a-input"
          placeholder="Admin key"
          autocomplete="current-password"
        />
        <button class="a-btn-primary" type="submit">Enter dashboard</button>
        <p v-if="authError" class="login-error">{{ authError }}</p>
      </form>
    </div>
  </div>

  <!-- ── Dashboard ── -->
  <div v-else class="dashboard">
    <!-- Header -->
    <div class="dash-header">
      <span class="dash-logo">ike. <span class="dash-logo-sub">// admin</span></span>
      <button class="a-btn-ghost" @click="logout">
        <LogOutIcon class="icon-sm" /> Logout
      </button>
    </div>

    <!-- Tabs -->
    <div class="dash-tabs">
      <button
        class="dash-tab"
        :class="{ 'dash-tab--active': activeTab === 'comments' }"
        @click="activeTab = 'comments'"
      >
        <MessageSquareIcon class="icon-sm" />
        Comments
        <span v-if="pendingComments.length" class="badge">{{ pendingComments.length }}</span>
      </button>
      <button
        class="dash-tab"
        :class="{ 'dash-tab--active': activeTab === 'poems' }"
        @click="activeTab = 'poems'"
      >
        <ScrollTextIcon class="icon-sm" />
        Poems
      </button>
      <button
        class="dash-tab"
        :class="{ 'dash-tab--active': activeTab === 'pinecone' }"
        @click="activeTab = 'pinecone'"
      >
        <DatabaseIcon class="icon-sm" />
        Pinecone
      </button>
      <button
        class="dash-tab"
        :class="{ 'dash-tab--active': activeTab === 'reading' }"
        @click="activeTab = 'reading'"
      >
        <BookOpenIcon class="icon-sm" />
        Reading
      </button>
    </div>

    <!-- ── Comments ── -->
    <section v-show="activeTab === 'comments'" class="dash-panel">
      <div class="panel-header">
        <p class="panel-label">// pending comments</p>
        <button class="a-btn-ghost" @click="loadComments">Refresh</button>
      </div>

      <div v-if="commentsLoading" class="loading-row">Loading…</div>

      <p v-else-if="!pendingComments.length" class="empty-hint">
        No pending comments. All clear.
      </p>

      <div v-else class="comment-list">
        <div v-for="c in pendingComments" :key="c.id" class="comment-card">
          <div class="comment-meta">
            <span class="comment-author">{{ c.author }}</span>
            <span class="comment-dot">·</span>
            <span class="comment-poem-id">"{{ poemTitleMap[c.poem_id] || c.poem_id.slice(0, 8) }}"</span>
            <span v-if="c.created_at" class="comment-date">· {{ c.created_at.slice(0, 10) }}</span>
          </div>
          <p class="comment-body">{{ c.body }}</p>
          <div class="comment-actions">
            <button class="a-btn-ok" @click="moderateComment(c.id, true)">
              <CheckIcon class="icon-xs" /> Approve
            </button>
            <button class="a-btn-danger" @click="moderateComment(c.id, false)">
              <XIcon class="icon-xs" /> Reject
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Poems ── -->
    <section v-show="activeTab === 'poems'" class="dash-panel">
      <div class="panel-header">
        <p class="panel-label">// poems</p>
        <button class="a-btn-primary" @click="showCreateForm = !showCreateForm">
          <PlusIcon class="icon-sm" /> New poem
        </button>
      </div>

      <!-- Create form -->
      <div v-if="showCreateForm" class="poem-form">
        <p class="form-section-label">New poem</p>
        <div class="form-row">
          <input v-model="createForm.title" class="a-input" placeholder="Title" />
          <label class="a-btn-ghost file-label">
            <UploadIcon class="icon-sm" /> Load .md
            <input type="file" accept=".md,.txt" class="sr-only"
              @change="(e) => loadMdFile(e.target, createForm)" />
          </label>
        </div>
        <input v-model="createForm.tags" class="a-input" placeholder="Tags, comma-separated" />
        <textarea v-model="createForm.excerpt" class="a-input a-textarea a-textarea--sm"
          placeholder="Excerpt (optional — auto-generated if blank)" />
        <textarea v-model="createForm.body" class="a-input a-textarea" placeholder="Full poem (markdown supported)" />
        <div class="form-actions">
          <button class="a-btn-primary" @click="createPoem">Create</button>
          <button class="a-btn-ghost" @click="showCreateForm = false">Cancel</button>
        </div>
      </div>

      <div v-if="poemsLoading" class="loading-row">Loading…</div>

      <p v-else-if="!allPoems.length" class="empty-hint">No poems yet.</p>

      <div v-else class="poem-table">
        <div class="poem-table-head">
          <span>Title</span>
          <span>Tags</span>
          <span class="col-num">Likes</span>
          <span></span>
        </div>

        <template v-for="poem in allPoems" :key="poem.id">
          <div class="poem-row">
            <span class="poem-row-title">{{ poem.title }}</span>
            <span class="poem-row-tags">
              <span v-for="t in poem.tags.slice(0,3)" :key="t" class="tag-chip">{{ t }}</span>
            </span>
            <span class="col-num poem-row-likes">{{ poem.likes }}</span>
            <div class="poem-row-actions">
              <button class="a-btn-icon" :title="editingPoemId === poem.id ? 'Cancel edit' : 'Edit'"
                @click="editingPoemId === poem.id ? cancelEdit() : startEdit(poem)">
                <PencilIcon class="icon-xs" />
              </button>
              <button class="a-btn-icon a-btn-icon--danger" title="Delete" @click="deletePoem(poem)">
                <Trash2Icon class="icon-xs" />
              </button>
            </div>
          </div>

          <!-- Inline edit form -->
          <div v-if="editingPoemId === poem.id" class="poem-form poem-form--edit">
            <div class="form-row">
              <input v-model="editForm.title" class="a-input" placeholder="Title" />
              <label class="a-btn-ghost file-label">
                <UploadIcon class="icon-sm" /> Load .md
                <input type="file" accept=".md,.txt" class="sr-only"
                  @change="(e) => loadMdFile(e.target, editForm)" />
              </label>
            </div>
            <input v-model="editForm.tags" class="a-input" placeholder="Tags, comma-separated" />
            <textarea v-model="editForm.excerpt" class="a-input a-textarea a-textarea--sm"
              placeholder="Excerpt" />
            <textarea v-model="editForm.body" class="a-input a-textarea" placeholder="Body (markdown)" />
            <div class="form-actions">
              <button class="a-btn-primary" @click="saveEdit(poem)">Save</button>
              <button class="a-btn-ghost" @click="cancelEdit">Cancel</button>
            </div>
          </div>
        </template>
      </div>
    </section>

    <!-- ── Pinecone ── -->
    <section v-show="activeTab === 'pinecone'" class="dash-panel">
      <div class="panel-header">
        <p class="panel-label">// pinecone</p>
        <button class="a-btn-ghost" @click="loadPineconeIndexes">Refresh</button>
      </div>

      <div v-if="pineconeLoading" class="loading-row">Loading indexes…</div>

      <div v-else class="pc-layout">
        <!-- Index + namespace selectors -->
        <div class="pc-selectors">
          <div class="selector-group">
            <label class="selector-label">Index</label>
            <div class="select-wrap">
              <select v-model="pcIndex" class="a-select" @change="pcSearchResults = []">
                <option v-for="(_, name) in pineconeIndexes" :key="name" :value="name">
                  {{ name }}
                </option>
              </select>
              <ChevronDownIcon class="select-icon" />
            </div>
          </div>

          <div class="selector-group">
            <label class="selector-label">Namespace</label>
            <div class="ns-row">
              <input v-model="pcNamespace" class="a-input" placeholder='default ""' />
              <div v-if="pineconeIndexes[pcIndex]?.namespaces?.length" class="ns-chips">
                <button
                  v-for="ns in pineconeIndexes[pcIndex].namespaces"
                  :key="ns"
                  class="ns-chip"
                  :class="{ 'ns-chip--active': pcNamespace === ns }"
                  @click="pcNamespace = ns; pcSearchResults = []"
                >{{ ns || '(default)' }}</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Search -->
        <div class="pc-section">
          <p class="pc-section-label">Search records</p>
          <div class="search-row">
            <input
              v-model="pcSearchQuery"
              class="a-input"
              placeholder="Enter a query to search records…"
              @keydown.enter="searchRecords"
            />
            <button class="a-btn-primary" :disabled="pcSearching" @click="searchRecords">
              <SearchIcon class="icon-sm" />
              {{ pcSearching ? 'Searching…' : 'Search' }}
            </button>
          </div>

          <p v-if="!pcSearchResults.length && !pcSearching" class="empty-hint">
            Results will appear here.
          </p>

          <div v-if="pcSearchResults.length" class="record-list">
            <div v-for="hit in pcSearchResults" :key="hit.id" class="record-row">
              <div class="record-content">
                <span class="record-id">{{ hit.id }}</span>
                <p class="record-text">{{ hit.text }}</p>
              </div>
              <button class="a-btn-icon a-btn-icon--danger" title="Delete" @click="deleteRecord(hit.id)">
                <Trash2Icon class="icon-xs" />
              </button>
            </div>
          </div>
        </div>

        <!-- Add record -->
        <div class="pc-section">
          <p class="pc-section-label">Add record</p>
          <p v-if="pcIndex === 'portfolio'" class="pc-hint">
            Use namespace <code>github:owner:repo:manual</code> for project context — the
            <code>:manual</code> suffix keeps it safe when the webhook re-ingests that repo.
          </p>
          <input v-model="pcAddId" class="a-input" placeholder="Record ID (optional — auto-generated if blank)" />
          <textarea
            v-model="pcAddText"
            class="a-input a-textarea"
            placeholder="Text content to embed and store…"
          />
          <button class="a-btn-primary" :disabled="pcAdding || !pcAddText.trim()" @click="addRecord">
            <PlusIcon class="icon-sm" />
            {{ pcAdding ? 'Adding…' : 'Add record' }}
          </button>
        </div>
      </div>
    </section>

    <!-- ── Reading ── -->
    <section v-show="activeTab === 'reading'" class="dash-panel">
      <div class="panel-header">
        <p class="panel-label">// reading list</p>
        <button class="a-btn-ghost" @click="loadReading">
          <RefreshCwIcon class="icon-sm" /> Refresh
        </button>
      </div>

      <div v-if="readingLoading" class="loading-row">Loading…</div>

      <template v-else>
        <!-- Current book form -->
        <div class="reading-section">
          <p class="reading-section-label">Currently reading</p>
          <div class="reading-form">
            <div class="form-row">
              <input v-model="currentForm.title" class="a-input" placeholder="Title" />
              <input v-model="currentForm.author" class="a-input" placeholder="Author" />
            </div>
            <div class="form-row">
              <div class="progress-field">
                <label class="field-label">Progress %</label>
                <input
                  v-model.number="currentForm.progress"
                  type="number"
                  min="0"
                  max="100"
                  class="a-input progress-input"
                  placeholder="0"
                />
              </div>
              <div class="since-field">
                <label class="field-label">Since (YYYY-MM)</label>
                <input v-model="currentForm.since" class="a-input" placeholder="2025-05" />
              </div>
            </div>
            <textarea
              v-model="currentForm.thoughts"
              class="a-input a-textarea a-textarea--sm"
              placeholder="Thoughts on the book…"
            />
            <input v-model="currentForm.cover" class="a-input" placeholder="Cover image URL (optional)" />
            <div class="form-actions">
              <button
                class="a-btn-primary"
                :disabled="savingCurrent"
                @click="saveCurrentBook"
              >
                {{ savingCurrent ? 'Saving…' : 'Save current book' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Recently finished -->
        <div class="reading-section">
          <p class="reading-section-label">Recently finished</p>

          <div v-if="!readingData.recent?.length" class="empty-hint">No books added yet.</div>

          <div v-else class="recent-table">
            <div v-for="book in readingData.recent" :key="book.id" class="recent-row">
              <div class="recent-info">
                <span class="recent-title">{{ book.title }}</span>
                <span class="recent-author">{{ book.author }}</span>
                <span v-if="book.finished_at" class="recent-date">{{ book.finished_at }}</span>
              </div>
              <button class="a-btn-icon a-btn-icon--danger" title="Remove" @click="deleteRecentBook(book.id)">
                <Trash2Icon class="icon-xs" />
              </button>
            </div>
          </div>

          <div class="reading-form" style="margin-top: 1rem;">
            <p class="form-section-label">Add book</p>
            <div class="form-row">
              <input v-model="recentForm.title" class="a-input" placeholder="Title" />
              <input v-model="recentForm.author" class="a-input" placeholder="Author" />
            </div>
            <input v-model="recentForm.finished_at" class="a-input" placeholder="Finished (YYYY-MM, optional)" />
            <div class="form-actions">
              <button
                class="a-btn-primary"
                :disabled="addingRecent || !recentForm.title || !recentForm.author"
                @click="addRecentBook"
              >
                {{ addingRecent ? 'Adding…' : 'Add' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Resume cache -->
        <div class="reading-section cache-card">
          <p class="reading-section-label">Resume cache</p>
          <p class="cache-note">Resume is parsed once and cached for 24 h. Force-refresh if you've updated your PDF.</p>
          <button
            class="a-btn-ghost"
            :disabled="clearingCache"
            @click="clearResumeCache"
          >
            <RefreshCwIcon class="icon-sm" />
            {{ clearingCache ? 'Clearing…' : 'Refresh now' }}
          </button>
        </div>
      </template>
    </section>

    <!-- Toast -->
    <transition name="toast">
      <div v-if="toast" class="toast" :class="{ 'toast--err': toast.type === 'err' }">
        {{ toast.msg }}
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* ── Tokens ──────────────────────────────────────────────────────────────── */
.dashboard, .login-wrap {
  min-height: 100vh;
  background: var(--theme-bg);
  color: var(--theme-text);
  font-size: 0.9rem;
}

/* ── Login ────────────────────────────────────────────────────────────────── */
.login-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-box {
  width: 100%;
  max-width: 360px;
  padding: 2rem 1.5rem;
  border: 1px solid rgb(var(--theme-white-rgb) / 0.07);
  border-radius: 12px;
  background: rgb(var(--theme-white-rgb) / 0.02);
  margin: 2rem;
}
.login-label {
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 1.5rem;
}
.login-form { display: flex; flex-direction: column; gap: 0.75rem; }
.login-error { font-size: 0.8125rem; color: var(--theme-danger); margin-top: 0.25rem; }

/* ── Dashboard shell ──────────────────────────────────────────────────────── */
.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgb(var(--theme-white-rgb) / 0.06);
}
.dash-logo {
  font-family: 'Syne', sans-serif;
  font-size: 1.125rem;
  font-weight: 800;
  color: var(--theme-text);
}
.dash-logo-sub {
  font-family: ui-monospace, monospace;
  font-size: 0.75rem;
  color: var(--theme-text-ghost);
  font-weight: 400;
  letter-spacing: 0.08em;
  margin-left: 0.5rem;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.dash-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  padding: 0 1.5rem;
}
.dash-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.75rem 1.25rem;
  font-size: 0.875rem;
  color: var(--theme-text-disabled);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.dash-tab:hover { color: var(--theme-text-muted); }
.dash-tab--active { color: var(--theme-text); border-bottom-color: var(--theme-accent); }

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  border-radius: 9999px;
  background: var(--theme-accent);
  color: var(--theme-on-accent);
  font-size: 0.6875rem;
  font-weight: 700;
}

/* ── Panel ────────────────────────────────────────────────────────────────── */
.dash-panel {
  max-width: 860px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
}
.panel-label {
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.loading-row { color: var(--theme-text-ghost); font-size: 0.875rem; padding: 1rem 0; }
.empty-hint { color: var(--theme-text-barely); font-size: 0.875rem; padding: 1rem 0; }

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.a-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.45rem 1rem;
  background: var(--theme-accent);
  color: var(--theme-on-accent);
  border: none;
  border-radius: 6px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: background 0.15s;
}
.a-btn-primary:hover { background: var(--theme-accent-hover); }
.a-btn-primary:disabled { opacity: 0.45; cursor: default; }

.a-btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.45rem 0.875rem;
  background: transparent;
  color: var(--theme-text-dim);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.09);
  border-radius: 6px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.a-btn-ghost:hover { color: var(--theme-text); border-color: rgb(var(--theme-white-rgb) / 0.18); }

.a-btn-ok {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.75rem;
  background: rgb(var(--theme-success-rgb) / 0.1);
  color: var(--theme-success);
  border: 1px solid rgb(var(--theme-success-rgb) / 0.25);
  border-radius: 6px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: background 0.15s;
}
.a-btn-ok:hover { background: rgb(var(--theme-success-rgb) / 0.18); }

.a-btn-danger {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.75rem;
  background: rgb(var(--theme-danger-rgb) / 0.1);
  color: var(--theme-danger);
  border: 1px solid rgb(var(--theme-danger-rgb) / 0.25);
  border-radius: 6px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: background 0.15s;
}
.a-btn-danger:hover { background: rgb(var(--theme-danger-rgb) / 0.18); }

.a-btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: transparent;
  color: var(--theme-text-disabled);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.07);
  border-radius: 6px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}
.a-btn-icon:hover { color: var(--theme-accent-soft); border-color: rgb(var(--theme-accent-rgb) / 0.3); background: rgb(var(--theme-accent-rgb) / 0.06); }
.a-btn-icon--danger:hover { color: var(--theme-danger); border-color: rgb(var(--theme-danger-rgb) / 0.3); background: rgb(var(--theme-danger-rgb) / 0.06); }

/* ── Inputs ───────────────────────────────────────────────────────────────── */
.a-input {
  width: 100%;
  padding: 0.55rem 0.875rem;
  background: rgb(var(--theme-white-rgb) / 0.04);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.08);
  border-radius: 6px;
  color: var(--theme-text);
  font-size: 0.875rem;
  box-sizing: border-box;
  transition: border-color 0.15s;
}
.a-input:focus { outline: none; border-color: rgb(var(--theme-accent-rgb) / 0.4); }
.a-input::placeholder { color: var(--theme-text-hidden); }
.a-textarea { min-height: 7rem; resize: vertical; font-family: inherit; }
.a-textarea--sm { min-height: 3.5rem; }

.a-select {
  appearance: none;
  width: 100%;
  padding: 0.55rem 2rem 0.55rem 0.875rem;
  background: rgb(var(--theme-white-rgb) / 0.04);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.08);
  border-radius: 6px;
  color: var(--theme-text);
  font-size: 0.875rem;
  cursor: pointer;
}
.a-select:focus { outline: none; border-color: rgb(var(--theme-accent-rgb) / 0.4); }
.select-wrap { position: relative; }
.select-icon {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: 0.875rem;
  height: 0.875rem;
  color: var(--theme-text-disabled);
  pointer-events: none;
}

.file-label {
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}
.sr-only {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0,0,0,0);
  border: 0;
}

/* ── Comments ─────────────────────────────────────────────────────────────── */
.comment-list { display: flex; flex-direction: column; gap: 0.75rem; }
.comment-card {
  padding: 1rem 1.25rem;
  background: rgb(var(--theme-white-rgb) / 0.02);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.07);
  border-radius: 8px;
}
.comment-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.8125rem;
  flex-wrap: wrap;
}
.comment-author { color: var(--theme-accent-soft); font-weight: 600; }
.comment-dot { color: var(--theme-text-barely); }
.comment-poem-id { color: var(--theme-text-ghost); font-family: ui-monospace, monospace; font-size: 0.75rem; }
.comment-date { color: var(--theme-text-barely); font-family: ui-monospace, monospace; font-size: 0.75rem; }
.comment-body { font-size: 0.9rem; color: var(--theme-text-dim); line-height: 1.6; margin-bottom: 0.875rem; }
.comment-actions { display: flex; gap: 0.5rem; }

/* ── Poems table ──────────────────────────────────────────────────────────── */
.poem-table {
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  border-radius: 8px;
  overflow: hidden;
}
.poem-table-head {
  display: grid;
  grid-template-columns: 1fr 160px 60px 72px;
  padding: 0.6rem 1rem;
  background: rgb(var(--theme-white-rgb) / 0.025);
  border-bottom: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  font-size: 0.75rem;
  color: var(--theme-text-ghost);
  font-family: ui-monospace, monospace;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.poem-row {
  display: grid;
  grid-template-columns: 1fr 160px 60px 72px;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgb(var(--theme-white-rgb) / 0.04);
  transition: background 0.1s;
}
.poem-row:last-child { border-bottom: none; }
.poem-row:hover { background: rgb(var(--theme-white-rgb) / 0.015); }
.poem-row-title { font-size: 0.9rem; color: var(--theme-text-soft); }
.poem-row-tags { display: flex; flex-wrap: wrap; gap: 0.25rem; }
.poem-row-likes { color: var(--theme-text-disabled); font-family: ui-monospace, monospace; font-size: 0.8125rem; }
.poem-row-actions { display: flex; gap: 0.375rem; justify-content: flex-end; }
.col-num { text-align: right; }

.tag-chip {
  font-size: 0.6875rem;
  padding: 0.15rem 0.45rem;
  border-radius: 9999px;
  background: rgb(var(--theme-white-rgb) / 0.04);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.07);
  color: var(--theme-text-faint);
}

/* Poem form */
.poem-form {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  padding: 1.25rem;
  background: rgb(var(--theme-accent-rgb) / 0.04);
  border: 1px solid rgb(var(--theme-accent-rgb) / 0.15);
  border-radius: 8px;
  margin-bottom: 1.25rem;
}
.poem-form--edit {
  margin: 0;
  border-radius: 0;
  border-top: none;
  border-left: none;
  border-right: none;
  border-bottom: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  background: rgb(var(--theme-accent-rgb) / 0.02);
}
.form-section-label {
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-accent);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.form-row {
  display: flex;
  gap: 0.625rem;
  align-items: center;
}
.form-row .a-input { flex: 1; }
.form-actions { display: flex; gap: 0.5rem; }

/* ── Pinecone ─────────────────────────────────────────────────────────────── */
.pc-layout { display: flex; flex-direction: column; gap: 2rem; }

.pc-selectors {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 1.25rem;
  align-items: start;
  padding: 1.25rem;
  background: rgb(var(--theme-white-rgb) / 0.02);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  border-radius: 8px;
}
@media (max-width: 600px) {
  .pc-selectors { grid-template-columns: 1fr; }
}
.selector-group { display: flex; flex-direction: column; gap: 0.5rem; }
.selector-label {
  font-size: 0.75rem;
  color: var(--theme-text-ghost);
  font-family: ui-monospace, monospace;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.ns-row { display: flex; flex-direction: column; gap: 0.5rem; }
.ns-chips { display: flex; flex-wrap: wrap; gap: 0.375rem; margin-top: 0.25rem; }
.ns-chip {
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  background: rgb(var(--theme-white-rgb) / 0.04);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.08);
  color: var(--theme-text-dim);
  cursor: pointer;
  transition: all 0.15s;
  font-family: ui-monospace, monospace;
}
.ns-chip:hover { border-color: rgb(var(--theme-accent-rgb) / 0.35); color: var(--theme-accent-soft); }
.ns-chip--active { background: rgb(var(--theme-accent-rgb) / 0.1); border-color: rgb(var(--theme-accent-rgb) / 0.35); color: var(--theme-accent-soft); }

.pc-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  background: rgb(var(--theme-white-rgb) / 0.02);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  border-radius: 8px;
}
.pc-section-label {
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 0.25rem;
}
.pc-hint {
  font-size: 0.8125rem;
  color: var(--theme-text-ghost);
  line-height: 1.6;
  padding: 0.6rem 0.875rem;
  background: rgb(var(--theme-accent-rgb) / 0.05);
  border: 1px solid rgb(var(--theme-accent-rgb) / 0.12);
  border-radius: 6px;
}
.pc-hint code {
  font-family: ui-monospace, monospace;
  font-size: 0.8em;
  color: var(--theme-accent);
  background: rgb(var(--theme-accent-rgb) / 0.1);
  padding: 0.1em 0.3em;
  border-radius: 3px;
}
.search-row { display: flex; gap: 0.625rem; align-items: center; }
.search-row .a-input { flex: 1; }

.record-list { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.25rem; }
.record-row {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgb(var(--theme-white-rgb) / 0.02);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  border-radius: 6px;
}
.record-content { flex: 1; min-width: 0; }
.record-id {
  font-size: 0.7rem;
  font-family: ui-monospace, monospace;
  color: var(--theme-text-ghost);
  margin-bottom: 0.25rem;
  display: block;
  word-break: break-all;
}
.record-text {
  font-size: 0.875rem;
  color: var(--theme-text-dim);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Reading ──────────────────────────────────────────────────────────────── */
.reading-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1.25rem;
  background: rgb(var(--theme-white-rgb) / 0.02);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  border-radius: 8px;
  margin-bottom: 1.25rem;
}
.reading-section-label {
  font-family: ui-monospace, monospace;
  font-size: 0.6875rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 0.25rem;
}
.reading-form {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}
.field-label {
  font-size: 0.75rem;
  color: var(--theme-text-ghost);
  font-family: ui-monospace, monospace;
  letter-spacing: 0.06em;
  margin-bottom: 0.25rem;
  display: block;
}
.progress-field, .since-field {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.progress-input { max-width: 100px; }

.recent-table { display: flex; flex-direction: column; gap: 0.5rem; }
.recent-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.875rem;
  background: rgb(var(--theme-white-rgb) / 0.02);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.05);
  border-radius: 6px;
}
.recent-info { flex: 1; display: flex; flex-direction: column; gap: 0.15rem; }
.recent-title { font-size: 0.875rem; color: var(--theme-text-soft); }
.recent-author { font-size: 0.8125rem; color: var(--theme-text-disabled); }
.recent-date { font-size: 0.75rem; color: var(--theme-text-barely); font-family: ui-monospace, monospace; }

.cache-card { margin-top: 0.5rem; }
.cache-note {
  font-size: 0.8125rem;
  color: var(--theme-text-ghost);
  line-height: 1.6;
  margin-bottom: 0.5rem;
}

/* ── Icons ────────────────────────────────────────────────────────────────── */
.icon-sm { width: 0.875rem; height: 0.875rem; flex-shrink: 0; }
.icon-xs { width: 0.75rem; height: 0.75rem; flex-shrink: 0; }

/* ── Toast ────────────────────────────────────────────────────────────────── */
.toast {
  position: fixed;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.6rem 1.25rem;
  background: rgb(var(--theme-accent-rgb) / 0.15);
  border: 1px solid rgb(var(--theme-accent-rgb) / 0.35);
  border-radius: 9999px;
  font-size: 0.875rem;
  color: var(--theme-text);
  backdrop-filter: blur(12px);
  z-index: 100;
  white-space: nowrap;
}
.toast--err {
  background: rgb(var(--theme-danger-rgb) / 0.12);
  border-color: rgb(var(--theme-danger-rgb) / 0.3);
  color: var(--theme-danger-soft);
}
.toast-enter-active, .toast-leave-active { transition: opacity 0.25s, transform 0.25s; }
.toast-enter-from { opacity: 0; transform: translateX(-50%) translateY(8px); }
.toast-leave-to  { opacity: 0; transform: translateX(-50%) translateY(8px); }
</style>
