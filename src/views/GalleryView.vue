<script setup>
import { computed, onMounted, ref } from 'vue'
import { HeartIcon, SendIcon, UploadIcon } from 'lucide-vue-next'

const apiBase = import.meta.env.VITE_API_BASE_URL || ''
const poems = ref([])
const selectedPoemId = ref(null)
const commentForms = ref({})
const uploadForm = ref({
  adminKey: '',
  title: '',
  excerpt: '',
  body: '',
  tags: '',
})

const selectedPoem = computed(
  () => poems.value.find((poem) => poem.id === selectedPoemId.value) || poems.value[0],
)

onMounted(loadPoems)

async function loadPoems() {
  const response = await fetch(`${apiBase}/api/gallery/poems`)
  if (!response.ok) return
  const data = await response.json()
  poems.value = Array.isArray(data) ? data : data.poems || []
  poems.value.forEach((poem) => {
    if (!commentForms.value[poem.id]) {
      commentForms.value[poem.id] = { author: '', body: '' }
    }
  })
  selectedPoemId.value = selectedPoemId.value || poems.value[0]?.id
}

async function uploadPoem() {
  const response = await fetch(`${apiBase}/api/gallery/poems`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Key': uploadForm.value.adminKey,
    },
    body: JSON.stringify({
      title: uploadForm.value.title,
      excerpt: uploadForm.value.excerpt,
      body: uploadForm.value.body,
      tags: uploadForm.value.tags
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
    }),
  })
  if (!response.ok) return
  uploadForm.value.title = ''
  uploadForm.value.excerpt = ''
  uploadForm.value.body = ''
  uploadForm.value.tags = ''
  await loadPoems()
}

async function likePoem(poem) {
  const response = await fetch(`${apiBase}/api/gallery/poems/${poem.id}/like`, {
    method: 'POST',
  })
  if (!response.ok) return
  const like = await response.json()
  poems.value = poems.value.map((item) =>
    item.id === like.poem_id ? { ...item, likes: like.likes } : item,
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
  commentForms.value[poem.id] = { author: '', body: '' }
}
</script>

<template>
  <section class="min-h-screen w-full bg-black text-white px-4 py-8 md:px-8">
    <div class="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[320px_1fr]">
      <aside class="border-r border-gray-800 pr-0 lg:pr-6">
        <div class="mb-6 flex items-center justify-between gap-3">
          <h1 class="text-3xl font-bold">Gallery</h1>
          <span class="text-sm text-gray-400">Poems</span>
        </div>

        <div class="space-y-3">
          <button
            v-for="poem in poems"
            :key="poem.id"
            type="button"
            class="w-full border border-gray-800 bg-gray-950 p-4 text-left transition hover:border-blue-400"
            :class="{ 'border-blue-500': selectedPoem?.id === poem.id }"
            @click="selectedPoemId = poem.id"
          >
            <h2 class="font-semibold text-orange-100">{{ poem.title }}</h2>
            <p class="mt-2 text-sm text-gray-400 line-clamp-3">{{ poem.excerpt }}</p>
          </button>
        </div>
      </aside>

      <main v-if="selectedPoem" class="grid gap-8 xl:grid-cols-[1fr_360px]">
        <article>
          <div class="mb-5 flex flex-wrap items-center gap-2">
            <span
              v-for="tag in selectedPoem.tags"
              :key="tag"
              class="border border-gray-700 px-2 py-1 text-xs text-gray-300"
            >
              {{ tag }}
            </span>
          </div>
          <h2 class="text-4xl font-bold text-orange-100">{{ selectedPoem.title }}</h2>
          <p class="mt-6 whitespace-pre-line text-lg leading-8 text-gray-200">
            {{ selectedPoem.body }}
          </p>
          <button
            type="button"
            class="mt-8 inline-flex items-center gap-2 border border-blue-700 px-4 py-2 text-blue-100 transition hover:bg-blue-950"
            @click="likePoem(selectedPoem)"
          >
            <HeartIcon class="h-4 w-4" />
            {{ selectedPoem.likes }} likes
          </button>

          <section class="mt-10">
            <h3 class="mb-4 text-xl font-semibold">Comments</h3>
            <div class="space-y-3">
              <p v-if="!selectedPoem.comments?.length" class="text-gray-500">
                No approved comments yet.
              </p>
              <div
                v-for="comment in selectedPoem.comments"
                :key="comment.id"
                class="border border-gray-800 p-3"
              >
                <p class="text-sm font-semibold text-gray-200">{{ comment.author }}</p>
                <p class="mt-1 text-gray-400">{{ comment.body }}</p>
              </div>
            </div>
          </section>
        </article>

        <aside class="space-y-8">
          <form class="space-y-3 border border-gray-800 p-4" @submit.prevent="submitComment(selectedPoem)">
            <h3 class="font-semibold">Leave a comment</h3>
            <input
              v-model="commentForms[selectedPoem.id].author"
              class="w-full border border-gray-700 bg-gray-950 px-3 py-2"
              placeholder="Name"
            />
            <textarea
              v-model="commentForms[selectedPoem.id].body"
              class="min-h-28 w-full border border-gray-700 bg-gray-950 px-3 py-2"
              placeholder="Comment"
            ></textarea>
            <button class="inline-flex items-center gap-2 bg-blue-700 px-4 py-2" type="submit">
              <SendIcon class="h-4 w-4" />
              Submit
            </button>
            <p class="text-xs text-gray-500">Comments appear after approval.</p>
          </form>

          <form class="space-y-3 border border-gray-800 p-4" @submit.prevent="uploadPoem">
            <h3 class="font-semibold">Upload poem</h3>
            <input
              v-model="uploadForm.adminKey"
              class="w-full border border-gray-700 bg-gray-950 px-3 py-2"
              placeholder="Admin key"
              type="password"
            />
            <input
              v-model="uploadForm.title"
              class="w-full border border-gray-700 bg-gray-950 px-3 py-2"
              placeholder="Title"
            />
            <input
              v-model="uploadForm.tags"
              class="w-full border border-gray-700 bg-gray-950 px-3 py-2"
              placeholder="Tags, comma separated"
            />
            <textarea
              v-model="uploadForm.excerpt"
              class="min-h-20 w-full border border-gray-700 bg-gray-950 px-3 py-2"
              placeholder="Excerpt"
            ></textarea>
            <textarea
              v-model="uploadForm.body"
              class="min-h-40 w-full border border-gray-700 bg-gray-950 px-3 py-2"
              placeholder="Poem"
            ></textarea>
            <button class="inline-flex items-center gap-2 bg-orange-700 px-4 py-2" type="submit">
              <UploadIcon class="h-4 w-4" />
              Upload
            </button>
          </form>
        </aside>
      </main>

      <main v-else class="flex min-h-80 items-center justify-center text-gray-500">
        No poems uploaded yet.
      </main>
    </div>
  </section>
</template>
