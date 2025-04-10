<script setup>
import { ref, onMounted, watch, computed } from 'vue'
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

const messages = ref({
  global: [], // For general chat
})

const newMessage = ref('')
const chatContainer = ref(null)
const inputRef = ref(null)

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

// Add initial message based on context
watch(
  () => props.isOpen,
  (val) => {
    const conversation = currentConversation.value
    if (conversation.length === 0) {
      if (props.projectContext) {
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

const sendMessage = async () => {
  if (!newMessage.value.trim()) return

  const conversation = currentConversation.value

  // Add user message
  conversation.push({
    type: 'human',
    content: newMessage.value,
  })

  // Clear input
  const userMessage = newMessage.value
  newMessage.value = ''

  try {
    // Show loading message with typing animation
    const loadingIndex =
      conversation.push({
        type: 'ai',
        content: '',
        isLoading: true,
      }) - 1

    // Call the FastAPI backend
    const response = await fetch(botUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        context: conversation.slice(0, -1),
      }),
    })
    let data = await response.text()
    console.log('Raw response data:', data) // Log the raw data

    if (!response.ok) {
      throw new Error(`API responded with status ${response.status}`)
    }

    // Explicitly replace escaped newlines with actual newlines
    data = data.replace(/\\n/g, '\n')

    // Replace loading message with actual response
    conversation[loadingIndex] = {
      type: 'ai',
      content: data,
      isLoading: false,
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
  <div
    :class="[
      'fixed z-50 transition-all duration-300 ease-in-out',
      'md:w-[400px] w-full md:max-w-[400px]',
      'flex flex-col bg-gray-900/95 backdrop-blur-md',
      'md:right-4 md:top-4 md:bottom-4 md:rounded-lg',
      isOpen ? 'top-0 bottom-0' : 'translate-x-full md:translate-y-full',
    ]"
  >
    <!-- Header -->
    <div class="flex items-center justify-between p-4 border-b border-gray-700">
      <h2 class="text-xl font-semibold text-white">
        {{
          props.projectContext ? `Chat about ${props.projectContext.name}` : 'Chat with Ikeoluwa'
        }}
      </h2>
      <button @click="emit('close')" class="p-1 rounded-full hover:bg-gray-700 transition-colors">
        <XIcon class="h-6 w-6 text-gray-400" />
      </button>
    </div>

    <!-- Messages -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
      <div
        v-for="(message, index) in currentConversation"
        :key="index"
        :class="[
          'max-w-[70%] rounded-lg p-3',
          message.type === 'human' ? 'bg-blue-600 text-white ml-auto' : 'bg-gray-700 text-gray-100',
        ]"
      >
        <template v-if="message.isLoading">
          <div class="typing-animation">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </template>
        <template v-else>
          <div
            class="prose prose-invert prose-sm max-w-full prose-p:my-1 prose-ul:my-2 prose-li:my-0.5 prose-a:text-blue-400"
            v-html="renderMarkdown(message.content)"
          ></div>
        </template>
      </div>
    </div>

    <!-- Input -->
    <div class="p-4 border-t border-gray-700">
      <form @submit.prevent="sendMessage" class="flex gap-2">
        <input
          ref="inputRef"
          v-model="newMessage"
          type="text"
          placeholder="Ask me anything..."
          class="flex-1 bg-gray-800 text-white rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          class="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
        >
          <SendIcon class="h-5 w-5" />
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* Custom scrollbar styling */
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.3) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.3);
  border-radius: 4px;
}

/* Typing animation */
.typing-animation {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-animation span {
  width: 8px;
  height: 8px;
  background-color: #fff;
  border-radius: 50%;
  animation: typing 1s infinite ease-in-out;
}

.typing-animation span:nth-child(1) {
  animation-delay: 0.2s;
}

.typing-animation span:nth-child(2) {
  animation-delay: 0.4s;
}

.typing-animation span:nth-child(3) {
  animation-delay: 0.6s;
}

@keyframes typing {
  0%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  50% {
    transform: translateY(-4px);
    opacity: 1;
  }
}
</style>

<style>
/* Global styles for markdown content */
.prose ul {
  list-style-type: disc;
  padding-left: 1.5em;
  margin: 0.75em 0;
}

.prose li {
  margin-bottom: 0.25em;
}

.prose li::marker {
  color: rgba(156, 163, 175, 0.8);
}

.prose p {
  margin-bottom: 0.75em;
}
</style>
