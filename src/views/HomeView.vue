<template>
  <section
    id="home"
    class="min-h-screen w-full flex flex-col items-center justify-center bg-black p-8"
    tabindex="0"
    @click.stop="handleViewSwitch('introduction')"
    @touchend="handleViewSwitch('introduction')"
    autofocus
  >
    <div class="w-full max-w-[90vw] md:max-w-[80vw] lg:max-w-[70vw]">
      <div class="text-white text-3xl md:text-6xl lg:text-8xl mb-6">
        <span class="text-green-500 font-semibold whitespace-nowrap">ikeoluwa@blucoder</span>:
        <span class="text-purple-300/90 whitespace-nowrap">/home</span>
        <span class="mr-2 whitespace-nowrap">$</span>
      </div>
      <div class="typing-container">
        <div
          class="animate-typing text-white/50 text-2xl md:text-5xl lg:text-7xl"
          @animationend="handleAnimationEnd"
        >
          >>{{ typingText }}
        </div>
      </div>
    </div>
    <!--    reflection container -->
    <div
      class="w-full max-w-[90vw] md:max-w-[80vw] lg:max-w-[70vw] rotate-x-180 blur-[3px] -mt-4 mask-b-from-10% mask-b-from-gray mask-b-to-gray-50/10"
    >
      <div class="typing-container">
        <div
          class="animate-typing text-white/50 text-2xl md:text-5xl lg:text-7xl"
          @animationend="handleAnimationEnd"
        >
          >>{{ typingText }}
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useToast } from 'vue-toastification'
import { POSITION } from 'vue-toastification'

const emit = defineEmits(['switch-view'])
const typingText = ref('bash hello_world.sh')
const toast = useToast()
let activeToast = null
let toastShown = ref(false)

const handleAnimationEnd = (event) => {
  if (!toastShown.value && event.target.classList.contains('animate-typing')) {
    activeToast = toast.info('Tap or press ENTER to continue...', {
      position: POSITION.BOTTOM_RIGHT,
      closeOnClick: true,
      pauseOnHover: true,
      toastClassName: ['toast-style'],
      showCloseButtonOnHover: true,
      timeout: 5000,
    })
    toastShown.value = true
  }
}

const handleKeyDown = (event) => {
  if (event.key === 'Enter') {
    handleViewSwitch('introduction')
  }
}

const handleViewSwitch = (view) => {
  if (activeToast) {
    toast.dismiss(activeToast)
    activeToast = null
  }
  emit('switch-view', view)
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  if (activeToast) {
    toast.dismiss(activeToast)
  }
})
</script>
<style>
.typing-container {
  display: inline-block;
  overflow: hidden;
}

.animate-typing {
  border-right: 0.1em solid white;
  white-space: nowrap;
  overflow: hidden;
  animation:
    typing 3s steps(20) forwards,
    blink 1s step-end infinite;
}

@keyframes typing {
  from {
    width: 0;
  }
  to {
    width: 100%;
  }
}

@keyframes blink {
  50% {
    border-color: transparent;
  }
}

.toast-style {
  background: #1c1c1c !important;
  backdrop-filter: blur(8px);
  color: green !important;
}

/* Remove outline on focused elements */
#home:focus {
  outline: none;
}
</style>
