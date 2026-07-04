<script setup>
import { ref, watch, computed } from 'vue'
import { XIcon, SendIcon } from 'lucide-vue-next'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
  html: true,
  typographer: true,
})

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  projectContext: {
    type: Object,
    default: null,
  },
})

const botUrl = import.meta.env.VITE_BOT_URL
const emit = defineEmits(['close'])
const CHAT_USER_MESSAGE_MAX_LENGTH = 1000

const messages = ref({
  global: [], // For general chat
})

const newMessage = ref('')
const chatContainer = ref(null)
const inputRef = ref(null)

const trimmedMessage = computed(() => newMessage.value.trim())
const messageLength = computed(() => newMessage.value.length)
const charactersRemaining = computed(() => CHAT_USER_MESSAGE_MAX_LENGTH - messageLength.value)
const isMessageTooLong = computed(() => messageLength.value > CHAT_USER_MESSAGE_MAX_LENGTH)
const canSendMessage = computed(() => trimmedMessage.value && !isMessageTooLong.value)

const projectDetailsForPrompt = computed(() => {
  if (!props.projectContext) return ''

  const project = props.projectContext
  const details = [
    `Project name: ${project.name || 'Unknown project'}`,
    project.type ? `Type: ${project.type}` : '',
    project.demo ? `Live demo: ${project.demo}` : '',
    project.source_code_url ? `Source code: ${project.source_code_url}` : '',
    project.video ? `Video: ${project.video}` : '',
    project.description ? `Description: ${project.description.replace(/<[^>]*>/g, ' ')}` : '',
  ].filter(Boolean)

  return details.join('\n')
})

// Get current conversation based on context
const currentConversation = computed(() => {
  if (props.projectContext) {
    // Initialize project messages array if it doesn't exist
    if (!messages.value[props.projectContext.name]) {
      messages.value[props.projectContext.name] = []
    }
    return messages.value[props.projectContext.name]
  }
  return messages.value.global
})

const visibleConversation = computed(() =>
  currentConversation.value.filter((message) => !message.hidden),
)

// Add initial message based on context
watch(
  () => props.isOpen,
  (val) => {
    const conversation = currentConversation.value
    if (conversation.length === 0) {
      if (props.projectContext) {
        conversation.push({
          type: 'human',
          content: `The user is viewing this project:\n${projectDetailsForPrompt.value}`,
          hidden: true,
        })
        conversation.push({
          type: 'ai',
          content: `Hi! 👋.I see you're curious about the "${props.projectContext.name}" project! What would you like to know? The architecture, deployment process, or maybe the inspiration behind it? Feel free to ask anything :)`,
        })
      } else {
        conversation.push({
          type: 'ai',
          content: `Hi there! 👋, you seem to be curious about something.Feel free to ask me about:
• My technical skills and experience
• Projects I've worked on
• My professional journey
• My interests and hobbies
• Or anything else you'd like to know!`,
        })
      }
    }
  },
)

// Focus input when chat opens
watch(
  () => props.isOpen,
  (newValue) => {
    if (newValue) {
      setTimeout(() => {
        inputRef.value?.focus()
      }, 300) // Wait for transition to complete
    }
  },
)

// Scroll to bottom when new messages are added
watch(
  () => currentConversation.value.length,
  () => {
    setTimeout(() => {
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
    }, 100)
  },
)

const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!canSendMessage.value) return

  const conversation = currentConversation.value

  conversation.push({ type: 'human', content: trimmedMessage.value })
  newMessage.value = ''

  const loadingIndex =
    conversation.push({ type: 'ai', content: '', isLoading: true }) - 1

  try {
    const response = await fetch(botUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ context: conversation.slice(0, -1) }),
    })

    if (!response.ok) {
      throw new Error(`API responded with status ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let firstChunk = true

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      if (firstChunk) {
        conversation[loadingIndex].isLoading = false
        firstChunk = false
      }
      conversation[loadingIndex].content += decoder.decode(value, { stream: true })
      scrollToBottom()
    }

    if (firstChunk) {
      conversation[loadingIndex].isLoading = false
    }
  } catch (error) {
    console.error('Error sending message:', error)
    conversation.pop()
    conversation.push({
      type: 'ai',
      content: 'Sorry, I encountered an error communicating with the AI. Please try again.',
      isLoading: false,
    })
  }
}

const renderMarkdown = (content) => {
  return md.render(content)
}

</script>

<template>
  <div class="chat-panel" :class="{ 'chat-panel--open': isOpen }">
    <!-- Header -->
    <div class="chat-header">
      <div class="chat-header-info">
        <span class="chat-label">// chat</span>
        <h2 class="chat-title">
          {{ props.projectContext ? props.projectContext.name : 'ask ike.' }}
        </h2>
      </div>
      <button class="chat-close" @click="emit('close')" aria-label="Close chat">
        <XIcon class="chat-close-icon" />
      </button>
    </div>

    <!-- Messages -->
    <div ref="chatContainer" class="chat-messages">
      <div
        v-for="(message, index) in visibleConversation"
        :key="index"
        class="chat-message"
        :class="message.type === 'human' ? 'chat-message--human' : 'chat-message--ai'"
      >
        <template v-if="message.isLoading">
          <div class="typing-animation">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </template>
        <template v-else>
          <div class="chat-markdown" v-html="renderMarkdown(message.content)"></div>
        </template>
      </div>
    </div>

    <!-- Input -->
    <div class="chat-input-area">
      <form class="chat-form" @submit.prevent="sendMessage">
        <input
          ref="inputRef"
          v-model="newMessage"
          type="text"
          placeholder="Ask me anything..."
          :maxlength="CHAT_USER_MESSAGE_MAX_LENGTH"
          class="chat-input"
        />
        <button type="submit" :disabled="!canSendMessage" class="chat-send">
          <SendIcon class="chat-send-icon" />
        </button>
      </form>
      <div class="chat-char-count">
        <span v-if="isMessageTooLong" class="chat-char-error">
          Message must be {{ CHAT_USER_MESSAGE_MAX_LENGTH }} characters or fewer.
        </span>
        <span v-else class="chat-char-hint">Keep messages under {{ CHAT_USER_MESSAGE_MAX_LENGTH }} characters.</span>
        <span class="chat-char-num" :class="{ 'chat-char-num--error': isMessageTooLong }">
          {{ charactersRemaining }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Panel */
.chat-panel {
  position: fixed;
  z-index: 50;
  display: flex;
  flex-direction: column;
  inset: 0;
  background: rgb(var(--theme-bg-rgb) / 0.97);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  transform: translateX(100%);
  transition: transform 0.3s ease-in-out;
}

.chat-panel--open {
  transform: translateX(0);
}

@media (min-width: 768px) {
  .chat-panel {
    inset: auto;
    top: 64px;
    right: 1rem;
    bottom: 1rem;
    left: auto;
    width: 400px;
    border-radius: 12px;
    border: 1px solid rgb(var(--theme-white-rgb) / 0.07);
    box-shadow: 0 8px 40px rgb(var(--theme-black-rgb) / 0.6);
    transform: translateY(110%);
  }

  .chat-panel--open {
    transform: translateY(0);
  }
}

/* Header */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  flex-shrink: 0;
}

.chat-header-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.chat-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.68rem;
  color: var(--theme-text-barely);
  letter-spacing: 0.05em;
}

.chat-title {
  font-family: 'Syne', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--theme-text);
  margin: 0;
  line-height: 1.2;
}

.chat-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  background: transparent;
  border: 1px solid rgb(var(--theme-white-rgb) / 0.07);
  color: var(--theme-text-disabled);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  flex-shrink: 0;
}

.chat-close:hover {
  border-color: rgb(var(--theme-white-rgb) / 0.14);
  color: var(--theme-text-muted);
}

.chat-close-icon {
  width: 14px;
  height: 14px;
}

/* Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  scrollbar-width: thin;
  scrollbar-color: rgb(var(--theme-accent-rgb) / 0.2) transparent;
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgb(var(--theme-accent-rgb) / 0.2);
  border-radius: 4px;
}

.chat-message {
  border-radius: 8px;
  padding: 0.7rem 0.9rem;
  font-size: 0.875rem;
  line-height: 1.65;
  min-width: 0;
  word-break: break-word;
}

.chat-message--human {
  background: rgb(var(--theme-accent-rgb) / 0.1);
  border: 1px solid rgb(var(--theme-accent-rgb) / 0.22);
  color: var(--theme-text-soft);
  align-self: flex-end;
  max-width: 82%;
}

.chat-message--ai {
  background: rgb(var(--theme-white-rgb) / 0.02);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  color: var(--theme-text-muted);
  align-self: stretch;
}

/* Typing animation */
.typing-animation {
  display: flex;
  gap: 5px;
  padding: 3px 0;
}

.typing-animation span {
  width: 7px;
  height: 7px;
  background: rgb(var(--theme-accent-rgb) / 0.7);
  border-radius: 50%;
  animation: typing 1s infinite ease-in-out;
}

.typing-animation span:nth-child(1) { animation-delay: 0.15s; }
.typing-animation span:nth-child(2) { animation-delay: 0.3s; }
.typing-animation span:nth-child(3) { animation-delay: 0.45s; }

@keyframes typing {
  0%, 100% { transform: translateY(0); opacity: 0.35; }
  50%       { transform: translateY(-5px); opacity: 1; }
}

/* Input area */
.chat-input-area {
  padding: 1rem 1.25rem;
  border-top: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  flex-shrink: 0;
}

.chat-form {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.chat-input {
  flex: 1;
  background: rgb(var(--theme-white-rgb) / 0.04);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.08);
  border-radius: 8px;
  padding: 0.5rem 0.875rem;
  font-size: 0.875rem;
  color: var(--theme-text);
  outline: none;
  min-width: 0;
  transition: border-color 0.15s;
}

.chat-input::placeholder {
  color: var(--theme-text-barely);
}

.chat-input:focus {
  border-color: rgb(var(--theme-accent-rgb) / 0.4);
}

.chat-send {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--theme-accent);
  border: none;
  color: var(--theme-on-accent);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, opacity 0.15s;
}

.chat-send:hover:not(:disabled) {
  background: var(--theme-accent-hover-alt);
}

.chat-send:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.chat-send-icon {
  width: 15px;
  height: 15px;
}

/* Char count */
.chat-char-count {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.45rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
}

.chat-char-hint { color: var(--theme-text-barely); }
.chat-char-error { color: rgb(var(--theme-danger-alt-rgb) / 0.65); }
.chat-char-num { color: var(--theme-text-disabled); }
.chat-char-num--error { color: rgb(var(--theme-danger-alt-rgb) / 0.65); }
</style>

<style>
/* Markdown content — unscoped because v-html bypasses scoped attribute */
.chat-markdown {
  min-width: 0;
  overflow-wrap: anywhere;
}

.chat-markdown p {
  margin: 0 0 0.65em;
}

.chat-markdown p:last-child {
  margin-bottom: 0;
}

.chat-markdown ul,
.chat-markdown ol {
  padding-left: 1.4em;
  margin: 0.5em 0;
}

.chat-markdown li {
  margin-bottom: 0.2em;
}

.chat-markdown li::marker {
  color: rgb(var(--theme-accent-rgb) / 0.5);
}

.chat-markdown a {
  color: var(--theme-accent);
  text-decoration: none;
}

.chat-markdown a:hover {
  text-decoration: underline;
}

.chat-markdown code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82em;
  background: rgb(var(--theme-accent-rgb) / 0.08);
  border: 1px solid rgb(var(--theme-accent-rgb) / 0.14);
  border-radius: 4px;
  padding: 0.1em 0.35em;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.chat-markdown pre {
  background: rgb(var(--theme-white-rgb) / 0.03);
  border: 1px solid rgb(var(--theme-white-rgb) / 0.06);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin: 0.5em 0;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: rgb(var(--theme-accent-rgb) / 0.2) transparent;
}

.chat-markdown pre::-webkit-scrollbar { height: 4px; }
.chat-markdown pre::-webkit-scrollbar-track { background: transparent; }
.chat-markdown pre::-webkit-scrollbar-thumb { background: rgb(var(--theme-accent-rgb) / 0.2); border-radius: 4px; }

.chat-markdown pre code {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.82em;
  white-space: pre;
  overflow-wrap: normal;
  display: block;
  min-width: max-content;
}
</style>
