<template>
  <section
    class="min-h-screen w-full flex flex-col lg:flex-row items-center justify-center bg-[var(--theme-bg)] p-8 md:gap-16 gap-8 m-4"
  >
    <div class="w-full max-w-[90dvw] md:max-w-[80dvw] lg:max-w-[70dvw] animate-slide-up">
      <div class="about-container">
        <h1 class="text-[rgb(var(--theme-white-rgb)/0.32)] text-xl md:text-3xl lg:text-4xl mb-8">&lt;about /&gt;</h1>

        <h2 class="text-[var(--theme-text)] text-lg md:text-xl lg:text-2xl mb-6">Ike here,👋</h2>

        <p class="text-[rgb(var(--theme-white-rgb)/0.8)] text-base md:text-lg lg:text-xl mb-8">
          I'm a student at
          <span class="text-[var(--theme-success)]">Algonquin College, Ottawa.</span>
          Currently pursuing an Advance Diploma in
          <span class="text-[var(--theme-text-ghost)] font-semibold"
            >Computer Engineering Technology-Computing Science</span
          >
          <span class="text-xs italic"> a mouthful, I know 😏</span>
        </p>

        <h3 class="text-[var(--theme-text)] text-base md:text-lg lg:text-xl mb-4">A bit about me:</h3>

        <ul class="text-[rgb(var(--theme-white-rgb)/0.8)] space-y-4 mb-8">
          <li class="flex items-start">
            <span class="text-[var(--theme-success)] mr-2">▸</span>
            <span
              >I'm currently an IT support intern at
              <span class="text-[var(--theme-success)]">Taggart Construction </span>.</span
            >
          </li>
          <li class="flex items-start">
            <span class="text-[var(--theme-success)] mr-2">▸</span>
            <span>My creativity comes from Absorption</span>
          </li>
          <li class="flex items-start">
            <span class="text-[var(--theme-success)] mr-2">▸</span>
            <span>I’m a perfectionist, and I struggle with imposter syndrome </span>
            <span class="text-xs italic self-end"> double homicide</span>
          </li>
          <li class="flex items-start">
            <span class="text-[var(--theme-success)] mr-2">▸</span>
            <span
              >I love math and llms, I find both fascinating, yet I do not know enough of them like
              I want to</span
            >
          </li>
        </ul>

        <div class="flex justify-center mt-8">
          <button
            @click="$emit('switch-view', 'introduction')"
            class="text-[var(--theme-text)] animate-bounce p-2 rounded-full hover:bg-[rgb(var(--theme-white-rgb)/0.1)] transition-colors"
          >
            <ChevronUp class="h-10 w-10 text-[var(--theme-text)] transition-colors duration-500"></ChevronUp>
          </button>
        </div>
      </div>
    </div>

    <div
      class="image-container w-full max-w-[90dvw] md:max-w-[80dvw] lg:max-w-[70dvw] flex justify-center animate-slide-up animation-delay-300"
    >
      <img
        src="https://res.cloudinary.com/dao2elffs/image/upload/v1744039966/portrait_w0cvte.jpg"
        alt="Profile image"
        class="w-full max-w-md rounded-lg shadow-xl"
      />
    </div>
  </section>
</template>

<script setup>
import { ChevronUp } from 'lucide-vue-next'
</script>

<style scoped>
.animate-slide-up {
  animation: slide-up 0.6s ease forwards;
}

.animation-delay-300 {
  animation-delay: 300ms;
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(50px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
