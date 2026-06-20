<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { HeartIcon, SendIcon } from 'lucide-vue-next'
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

const route = useRoute()
const apiBase = import.meta.env.VITE_API_BASE_URL || ''

const poem = ref(null)
const commentForms = ref({})
const pendingComments = ref({})
const loading = ref(true)

const renderedBody = computed(() => {
  if (!poem.value?.body) return ''
  return md.render(poem.value.body)
})

onMounted(() => {
  loadPoem()
})

async function loadPoem() {
  loading.value = true
  try {
    const response = await fetch(`${apiBase}/api/gallery/poems/${route.params.poemId}`)
    if (!response.ok) throw new Error()
    poem.value = await response.json()
  } catch {
    poem.value = PLACEHOLDER_POEMS.find((entry) => entry.id === route.params.poemId) || null
  } finally {
    if (poem.value && !commentForms.value[poem.value.id]) {
      commentForms.value[poem.value.id] = { author: '', body: '' }
    }
    loading.value = false
  }
}

async function likePoem() {
  if (!poem.value) return
  const response = await fetch(`${apiBase}/api/gallery/poems/${poem.value.id}/like`, {
    method: 'POST',
  })
  if (!response.ok) return
  const like = await response.json()
  poem.value = { ...poem.value, likes: like.likes }
}

async function submitComment() {
  if (!poem.value) return
  const form = commentForms.value[poem.value.id]
  if (!form?.author || !form?.body) return

  const response = await fetch(`${apiBase}/api/gallery/poems/${poem.value.id}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form),
  })
  if (!response.ok) return

  if (!pendingComments.value[poem.value.id]) pendingComments.value[poem.value.id] = []
  pendingComments.value[poem.value.id].push({ author: form.author, body: form.body })
  commentForms.value[poem.value.id] = { author: '', body: '' }
}
</script>

<template>
  <div class="poem-page">
    <div v-if="loading" class="poem-page-empty">Loading poem...</div>

    <article v-else-if="poem" class="poem-shell">
      <div class="poem-tags">
        <span
          v-for="tag in poem.tags"
          :key="tag"
          class="tag-pill"
        >{{ tag }}</span>
      </div>

      <h1 class="poem-title">{{ poem.title }}</h1>
      <div class="poem-body" v-html="renderedBody"></div>

      <button
        type="button"
        class="like-btn"
        @click="likePoem"
      >
        <HeartIcon class="h-4 w-4" />
        {{ poem.likes }} {{ poem.likes === 1 ? 'like' : 'likes' }}
      </button>

      <section class="comments-section">
        <h2 class="comments-heading">Comments</h2>
        <p
          v-if="!poem.comments?.length && !pendingComments[poem.id]?.length"
          class="empty-comments"
        >
          No comments yet.
        </p>

        <div
          v-for="comment in poem.comments"
          :key="comment.id"
          class="comment"
        >
          <p class="comment-author">{{ comment.author }}</p>
          <p class="comment-body">{{ comment.body }}</p>
        </div>

        <div
          v-for="(comment, i) in pendingComments[poem.id]"
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

      <form class="comment-form" @submit.prevent="submitComment">
        <h2 class="form-heading">Leave a comment</h2>
        <input
          v-model="commentForms[poem.id].author"
          class="form-input"
          placeholder="Your name"
        />
        <textarea
          v-model="commentForms[poem.id].body"
          class="form-input form-textarea"
          placeholder="Your comment"
        />
        <div class="form-footer">
          <button class="submit-btn" type="submit">
            <SendIcon class="h-3.5 w-3.5" />
            Submit
          </button>
          <p v-if="!pendingComments[poem.id]?.length" class="form-note">
            Comments appear after approval.
          </p>
        </div>
      </form>
    </article>

    <div v-else class="poem-page-empty">Poem not found.</div>
  </div>
</template>

<style scoped>
.poem-page {
  max-width: 760px;
  margin: 0 auto;
  padding: 2rem 1.25rem 4rem;
}

.poem-shell {
  display: flex;
  flex-direction: column;
}

.poem-page-empty {
  color: #42405a;
  font-size: 0.95rem;
  padding: 3rem 0;
}

.poem-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 1.125rem;
}

.tag-pill {
  font-size: 0.7rem;
  padding: 0.2rem 0.55rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  color: #6a6878;
  letter-spacing: 0.02em;
}

.poem-title {
  font-family: 'Syne', sans-serif;
  font-size: clamp(2rem, 8vw, 3rem);
  font-weight: 800;
  color: #e0ddf5;
  margin-bottom: 1.5rem;
  line-height: 1.05;
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
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  margin: 1.5rem 0;
}

.like-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  width: fit-content;
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

.comments-section { margin-bottom: 2rem; }

.comments-heading,
.form-heading {
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

.comment-body {
  font-size: 0.875rem;
  color: #7a7888;
  line-height: 1.6;
}

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

.comment-form {
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
</style>
