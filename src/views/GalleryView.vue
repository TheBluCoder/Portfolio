<script setup>
import { computed, onMounted, ref } from 'vue'
import { HeartIcon, SendIcon, BookOpenIcon, ScrollTextIcon } from 'lucide-vue-next'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ breaks: true, linkify: false })

const PLACEHOLDER_POEMS = [
  {
    id: '__placeholder_1',
    title: 'Latency',
    excerpt: 'Every promise made is a function waiting to return.',
    body: `Every promise made\nis a function\nwaiting to return.\n\nI have learned patience\nfrom async/await—\nhow to say *I'll get back to you*\nand mean it.\n\nThe event loop doesn't panic.\nIt just keeps checking,\nquietly,\nif anything is ready.\n\nI am trying to be\nmore like that.`,
    tags: ['dev', 'patience'],
    likes: 4,
    comments: [],
    created_at: null,
  },
  {
    id: '__placeholder_2',
    title: 'push --force',
    excerpt: 'You can rewrite history, they said. But the remote remembers.',
    body: `You can rewrite history,\nthey said.\n\nSo I did.\nScrubbed the commit message,\npretended the mistake\nnever existed—\n\nbut the remote remembers.\nOrigin always does.\n\nAnd someone, somewhere,\nhad already pulled.`,
    tags: ['dev', 'regret'],
    likes: 7,
    comments: [],
    created_at: null,
  },
  {
    id: '__placeholder_3',
    title: '3 AM',
    excerpt: 'The bug was a missing comma. Three hours for a comma.',
    body: `The bug was a missing comma.\nThree hours for a comma.\n\nAt 3 AM the screen is\nthe only sun,\nand you start to think\nyou are the only person\nawake in the world.\n\nYou are not.\nSomewhere, another light is on.\nAnother person is talking\nto a rubber duck\nabout state management.\n\nThis is community.`,
    tags: ['life', 'dev'],
    likes: 12,
    comments: [
      { id: 'c1', poem_id: '__placeholder_3', author: 'Tobi', body: 'The rubber duck line got me.', approved: true, created_at: null },
    ],
    created_at: null,
  },
  {
    id: '__placeholder_4',
    title: 'Merge Conflict',
    excerpt: 'Two versions of yourself, both correct, unable to reconcile.',
    body: `Two versions of yourself,\nboth correct,\nunable to reconcile.\n\nThe person you were in January\nhas opinions about the person\nyou are in June.\n\nYou must choose,\nline by line,\nwhich self to keep—\n\nand commit.`,
    tags: ['life'],
    likes: 9,
    comments: [],
    created_at: null,
  },
]

const _READING_DEFAULT = {
  current: {
    title: "The Pragmatic Programmer",
    author: "David Thomas & Andrew Hunt",
    cover: null,
    thoughts: "A book about becoming a better programmer — not through tools, but through habits of mind. Working through it slowly.",
    progress: 40,
    since: "2025-05",
  },
  recent: [],
}

const apiBase = import.meta.env.VITE_API_BASE_URL || ''
const activeTab = ref('poems')

const readingData = ref(_READING_DEFAULT)
const readingLoading = ref(true)
const poems = ref([])
const selectedPoemId = ref(null)
const commentForms = ref({})
const pendingComments = ref({}) // keyed by poem ID — only visible to the submitter this session

const selectedPoem = computed(
  () => poems.value.find((p) => p.id === selectedPoemId.value) || poems.value[0],
)

const renderedBody = computed(() => {
  if (!selectedPoem.value?.body) return ''
  return md.render(selectedPoem.value.body)
})

onMounted(() => {
  loadPoems()
  loadReading()
})

async function loadPoems() {
  try {
    const response = await fetch(`${apiBase}/api/gallery/poems`)
    if (!response.ok) throw new Error()
    const data = await response.json()
    const loaded = Array.isArray(data) ? data : data.poems || []
    poems.value = loaded.length ? loaded : PLACEHOLDER_POEMS
  } catch {
    poems.value = PLACEHOLDER_POEMS
  }
  poems.value.forEach((poem) => {
    if (!commentForms.value[poem.id]) {
      commentForms.value[poem.id] = { author: '', body: '' }
    }
  })
  selectedPoemId.value = selectedPoemId.value || poems.value[0]?.id
}

async function likePoem(poem) {
  const response = await fetch(`${apiBase}/api/gallery/poems/${poem.id}/like`, {
    method: 'POST',
  })
  if (!response.ok) return
  const like = await response.json()
  poems.value = poems.value.map((p) =>
    p.id === like.poem_id ? { ...p, likes: like.likes } : p,
  )
}

async function submitComment(poem) {
  const form = commentForms.value[poem.id]
  if (!form?.author || !form?.body) return
  const response = await fetch(`${apiBase}/api/gallery/poems/${poem.id}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form),
  })
  if (!response.ok) return
  if (!pendingComments.value[poem.id]) pendingComments.value[poem.id] = []
  pendingComments.value[poem.id].push({ author: form.author, body: form.body })
  commentForms.value[poem.id] = { author: '', body: '' }
}

async function loadReading() {
  readingLoading.value = true
  try {
    const res = await fetch(`${apiBase}/api/reading`)
    if (!res.ok) throw new Error()
    readingData.value = await res.json()
  } catch {
    readingData.value = _READING_DEFAULT
  } finally {
    readingLoading.value = false
  }
}

const readingProgress = computed(() => {
  const pct = Math.max(0, Math.min(100, readingData.value?.current?.progress || 0))
  return pct
})
</script>

<template>
  <div class="gallery">
    <!-- ─── Tab bar ─── -->
    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'poems' }"
        @click="activeTab = 'poems'"
      >
        <ScrollTextIcon class="tab-icon" />
        Poems
      </button>
      <button
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === 'reading' }"
        @click="activeTab = 'reading'"
      >
        <BookOpenIcon class="tab-icon" />
        Reading
      </button>
    </div>

    <!-- ══════════════════════════════════════
         TAB: Poems
    ══════════════════════════════════════ -->
    <div v-show="activeTab === 'poems'" class="poems-layout">
      <!-- Sidebar list -->
      <aside class="poems-sidebar">
        <div
          v-if="!poems.length"
          class="empty-state"
        >No poems uploaded yet.</div>

        <button
          v-for="poem in poems"
          :key="poem.id"
          type="button"
          class="poem-card"
          :class="{ 'poem-card--active': selectedPoem?.id === poem.id }"
          @click="selectedPoemId = poem.id"
        >
          <h2 class="poem-card-title">{{ poem.title }}</h2>
          <p class="poem-card-excerpt">{{ poem.excerpt }}</p>
          <div class="poem-card-meta">
            <span
              v-for="tag in poem.tags.slice(0, 3)"
              :key="tag"
              class="tag-pill"
            >{{ tag }}</span>
          </div>
        </button>
      </aside>

      <!-- Detail pane -->
      <main v-if="selectedPoem" class="poem-detail">
        <div class="poem-tags">
          <span
            v-for="tag in selectedPoem.tags"
            :key="tag"
            class="tag-pill"
          >{{ tag }}</span>
        </div>
        <h2 class="poem-title">{{ selectedPoem.title }}</h2>
        <div class="poem-body" v-html="renderedBody"></div>

        <button
          type="button"
          class="like-btn"
          @click="likePoem(selectedPoem)"
        >
          <HeartIcon class="h-4 w-4" />
          {{ selectedPoem.likes }} {{ selectedPoem.likes === 1 ? 'like' : 'likes' }}
        </button>

        <!-- Comments -->
        <section class="comments-section">
          <h3 class="comments-heading">Comments</h3>
          <p
            v-if="!selectedPoem.comments?.length && !pendingComments[selectedPoem.id]?.length"
            class="empty-comments"
          >
            No comments yet.
          </p>

          <div
            v-for="comment in selectedPoem.comments"
            :key="comment.id"
            class="comment"
          >
            <p class="comment-author">{{ comment.author }}</p>
            <p class="comment-body">{{ comment.body }}</p>
          </div>

          <div
            v-for="(comment, i) in pendingComments[selectedPoem.id]"
            :key="'pending-' + i"
            class="comment comment--pending"
          >
            <p class="comment-author">
              {{ comment.author }}
              <span class="pending-badge">pending</span>
            </p>
            <p class="comment-body">{{ comment.body }}</p>
          </div>
        </section>

        <!-- Comment form -->
        <form class="comment-form" @submit.prevent="submitComment(selectedPoem)">
          <h3 class="form-heading">Leave a comment</h3>
          <input
            v-model="commentForms[selectedPoem.id].author"
            class="form-input"
            placeholder="Your name"
          />
          <textarea
            v-model="commentForms[selectedPoem.id].body"
            class="form-input form-textarea"
            placeholder="Your comment"
          />
          <div class="form-footer">
            <button class="submit-btn" type="submit">
              <SendIcon class="h-3.5 w-3.5" />
              Submit
            </button>
            <p v-if="!pendingComments[selectedPoem.id]?.length" class="form-note">
              Comments appear after approval.
            </p>
          </div>
        </form>

      </main>

      <main v-else-if="!poems.length" class="poems-empty">
        Nothing here yet.
      </main>
    </div>

    <!-- ══════════════════════════════════════
         TAB: Reading
    ══════════════════════════════════════ -->
    <div v-show="activeTab === 'reading'" class="reading-tab">
      <p class="section-label">// currently reading</p>

      <div v-if="readingLoading" class="reading-skeleton">
        <div class="skeleton-card"></div>
      </div>

      <div v-else class="reading-card">
        <!-- Cover placeholder -->
        <div class="book-cover">
          <BookOpenIcon class="book-cover-icon" />
        </div>

        <div class="book-info">
          <h2 class="book-title">{{ readingData.current.title }}</h2>
          <p class="book-author">by {{ readingData.current.author }}</p>

          <!-- Progress bar -->
          <div class="progress-wrap">
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: readingProgress + '%' }"
              />
            </div>
            <span class="progress-label">{{ readingProgress }}%</span>
          </div>
          <p class="book-since">Started {{ readingData.current.since }}</p>

          <p v-if="readingData.current.thoughts" class="book-thoughts">
            "{{ readingData.current.thoughts }}"
          </p>
        </div>
      </div>

      <!-- Recently finished -->
      <div v-if="!readingLoading && readingData.recent?.length" class="recent-books">
        <p class="section-label" style="margin-top: 2.5rem;">// recently finished</p>
        <div class="recent-list">
          <div
            v-for="book in readingData.recent"
            :key="book.id || book.title"
            class="recent-book"
          >
            <p class="recent-book-title">{{ book.title }}</p>
            <p class="recent-book-author">{{ book.author }}</p>
          </div>
        </div>
      </div>

      <div v-if="!readingLoading && !readingData.recent?.length" class="recent-empty">
        <p>More to come here as I read.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Outer wrapper ── */
.gallery {
  max-width: 1100px;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}

/* ── Tab bar ── */
.tab-bar {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 2.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding-bottom: 0;
}
.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
  color: #52506a;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.tab-btn:hover { color: #9896b0; }
.tab-btn--active {
  color: #e0ddf5;
  border-bottom-color: #8b7cf8;
}
.tab-icon {
  width: 0.9375rem;
  height: 0.9375rem;
}

/* ── Section label ── */
.section-label {
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-size: 0.6875rem;
  color: #3e3c52;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 1.5rem;
}

/* ── Poems layout ── */
.poems-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 2rem;
  align-items: start;
}
@media (max-width: 768px) {
  .poems-layout {
    grid-template-columns: 1fr;
  }
}

/* Sidebar */
.poems-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.poem-card {
  width: 100%;
  text-align: left;
  padding: 1rem 1.125rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.poem-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.1);
}
.poem-card--active {
  background: rgba(139, 124, 248, 0.06);
  border-color: rgba(139, 124, 248, 0.25);
}
.poem-card-title {
  font-family: 'Syne', sans-serif;
  font-size: 0.9375rem;
  font-weight: 700;
  color: #e0ddf5;
  margin-bottom: 0.375rem;
}
.poem-card-excerpt {
  font-size: 0.8125rem;
  color: #6a6878;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 0.625rem;
}
.poem-card-meta { display: flex; flex-wrap: wrap; gap: 0.3rem; }

/* Tags */
.tag-pill {
  font-size: 0.7rem;
  padding: 0.2rem 0.55rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  color: #6a6878;
  letter-spacing: 0.02em;
}

/* Poem detail */
.poem-detail {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.poem-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 1.125rem;
}
.poem-title {
  font-family: 'Syne', sans-serif;
  font-size: clamp(1.5rem, 4vw, 2.25rem);
  font-weight: 800;
  color: #e0ddf5;
  margin-bottom: 1.5rem;
  line-height: 1.15;
}
.poem-body {
  font-size: 1rem;
  color: #9896b0;
  line-height: 2;
  margin-bottom: 2rem;
  max-width: 55ch;
}
.poem-body :deep(p) {
  margin-bottom: 1.25rem;
  white-space: pre-line;
}
.poem-body :deep(em) { color: #b5aef8; font-style: italic; }
.poem-body :deep(strong) { color: #e0ddf5; font-weight: 600; }
.poem-body :deep(h1),
.poem-body :deep(h2),
.poem-body :deep(h3) {
  font-family: 'Syne', sans-serif;
  color: #e0ddf5;
  margin-bottom: 0.75rem;
  line-height: 1.2;
}
.poem-body :deep(blockquote) {
  border-left: 2px solid rgba(139, 124, 248, 0.3);
  padding-left: 1rem;
  color: #7a7888;
  font-style: italic;
  margin: 1rem 0;
}
.poem-body :deep(hr) {
  border: none;
  border-top: 1px solid rgba(255,255,255,0.06);
  margin: 1.5rem 0;
}

/* Like */
.like-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 1rem;
  font-size: 0.8125rem;
  color: #8884a0;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 9999px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  margin-bottom: 2.5rem;
}
.like-btn:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #e0ddf5;
}

/* Comments */
.comments-section { margin-bottom: 2rem; }
.comments-heading, .form-heading {
  font-family: 'Syne', sans-serif;
  font-size: 0.9375rem;
  font-weight: 700;
  color: #c8c6e0;
  margin-bottom: 1rem;
}
.empty-comments {
  font-size: 0.875rem;
  color: #42405a;
}
.comment {
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  margin-bottom: 0.5rem;
}
.comment-author {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #b8b5d0;
  margin-bottom: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.comment-body { font-size: 0.875rem; color: #7a7888; line-height: 1.6; }

.comment--pending {
  opacity: 0.65;
  border-color: rgba(139, 124, 248, 0.15);
  background: rgba(139, 124, 248, 0.03);
}
.pending-badge {
  font-size: 0.6rem;
  font-family: ui-monospace, monospace;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #8b7cf8;
  background: rgba(139, 124, 248, 0.12);
  border: 1px solid rgba(139, 124, 248, 0.2);
  padding: 0.1rem 0.4rem;
  border-radius: 9999px;
  font-weight: 500;
}

/* Forms */
.comment-form, .upload-form {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.015);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  margin-bottom: 1rem;
}
.form-input {
  width: 100%;
  padding: 0.55rem 0.875rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: #e0ddf5;
  font-size: 0.875rem;
  transition: border-color 0.15s;
  box-sizing: border-box;
}
.form-input:focus {
  outline: none;
  border-color: rgba(139, 124, 248, 0.4);
}
.form-input::placeholder { color: #42405a; }
.form-textarea { min-height: 6rem; resize: vertical; }
.form-textarea--sm { min-height: 4rem; }
.form-footer {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.form-note { font-size: 0.75rem; color: #3e3c52; }

.submit-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  background: #8b7cf8;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: background 0.15s;
}
.submit-btn:hover { background: #9d90fa; }

.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.07);
  color: #c8c6e0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: background 0.15s;
}
.upload-btn:hover { background: rgba(255, 255, 255, 0.1); }

.empty-state, .poems-empty {
  color: #42405a;
  font-size: 0.9rem;
  padding: 2rem 0;
}

/* ── Reading tab ── */
.reading-tab {
  max-width: 560px;
}
.reading-card {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
}
@media (max-width: 480px) {
  .reading-card { flex-direction: column; }
}
.book-cover {
  flex-shrink: 0;
  width: 80px;
  height: 112px;
  border-radius: 4px;
  background: rgba(139, 124, 248, 0.1);
  border: 1px solid rgba(139, 124, 248, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}
.book-cover-icon {
  width: 2rem;
  height: 2rem;
  color: rgba(139, 124, 248, 0.5);
}
.book-info { flex: 1; display: flex; flex-direction: column; gap: 0.5rem; }
.book-title {
  font-family: 'Syne', sans-serif;
  font-size: 1.0625rem;
  font-weight: 700;
  color: #e0ddf5;
  line-height: 1.3;
}
.book-author { font-size: 0.875rem; color: #6a6878; }

/* Progress */
.progress-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.25rem;
}
.progress-bar {
  flex: 1;
  height: 4px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.07);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #8b7cf8;
  border-radius: 9999px;
  transition: width 0.6s ease;
}
.progress-label { font-size: 0.75rem; color: #6a6878; font-family: ui-monospace, monospace; white-space: nowrap; }
.book-since { font-size: 0.75rem; color: #3e3c52; font-family: ui-monospace, monospace; }
.book-thoughts {
  font-size: 0.875rem;
  color: #6a6878;
  line-height: 1.65;
  font-style: italic;
  border-left: 2px solid rgba(139, 124, 248, 0.25);
  padding-left: 0.75rem;
  margin-top: 0.25rem;
}

.recent-list { display: flex; flex-direction: column; gap: 0.625rem; }
.recent-book {
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 6px;
}
.recent-book-title { font-size: 0.875rem; color: #c8c6e0; margin-bottom: 0.2rem; }
.recent-book-author { font-size: 0.8125rem; color: #52506a; }

.recent-empty {
  margin-top: 2rem;
  font-size: 0.875rem;
  color: #3e3c52;
  font-style: italic;
}

.reading-skeleton { margin-bottom: 1rem; }
.skeleton-card {
  height: 140px;
  border-radius: 10px;
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.06) 50%, rgba(255,255,255,0.03) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
