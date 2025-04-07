<template>
  <div
    class="fixed -bottom-1 left-[50%] -translate-x-1/2 mt-6 flex items-center justify-center gap-4 z-50"
  >
    <a
      href="https://www.linkedin.com/in/ikeoluwa-oladele-15100820a/"
      target="_blank"
      class="social-icon-link animate"
    >
      <LinkedinIcon class="w-8 h-8" />
    </a>
    <a href="mailto:oladeleikeoluwa508@gmail.com" class="social-icon-link animate">
      <MailIcon class="w-8 h-8" />
    </a>
    <button
      @click="$emit('open-chat') && (hide_waving_icon = 'true')"
      class="social-icon-link animate"
    >
      <MessageCircleIcon class="w-8 h-8" />
    </button>
    <a
      href="https://canary.discord.com/channels/@me"
      target="_blank"
      class="social-icon-link animate"
    >
      <div class="w-8 h-8 flex items-center justify-center">
        <svg viewBox="0 -28.5 256 256" class="w-6 h-6">
          <path
            d="M216.856339,16.5966031 C200.285002,8.84328665 182.566144,3.2084988 164.041564,0 C161.766523,4.11318106 159.108624,9.64549908 157.276099,14.0464379 C137.583995,11.0849896 118.072967,11.0849896 98.7430163,14.0464379 C96.9108417,9.64549908 94.1925838,4.11318106 91.8971895,0 C73.3526068,3.2084988 55.6133949,8.86399117 39.0420583,16.6376612 C5.61752293,67.146514 -3.4433191,116.400813 1.08711069,164.955721 C23.2560196,181.510915 44.7403634,191.567697 65.8621325,198.148576 C71.0772151,190.971126 75.7283628,183.341335 79.7352139,175.300261 C72.104019,172.400575 64.7949724,168.822202 57.8887866,164.667963 C59.7209612,163.310589 61.5131304,161.891452 63.2445898,160.431257 C105.36741,180.133187 151.134928,180.133187 192.754523,160.431257 C194.506336,161.891452 196.298154,163.310589 198.110326,164.667963 C191.183787,168.842556 183.854737,172.420929 176.223542,175.320965 C180.230393,183.341335 184.861538,190.991831 190.096624,198.16893 C211.238746,191.588051 232.743023,181.531619 254.911949,164.955721 C260.227747,108.668201 245.831087,59.8662432 216.856339,16.5966031 Z M85.4738752,135.09489 C72.8290281,135.09489 62.4592217,123.290155 62.4592217,108.914901 C62.4592217,94.5396472 72.607595,82.7145587 85.4738752,82.7145587 C98.3405064,82.7145587 108.709962,94.5189427 108.488529,108.914901 C108.508531,123.290155 98.3405064,135.09489 85.4738752,135.09489 Z M170.525237,135.09489 C157.88039,135.09489 147.510584,123.290155 147.510584,108.914901 C147.510584,94.5396472 157.658606,82.7145587 170.525237,82.7145587 C183.391518,82.7145587 193.761324,94.5189427 193.539891,108.914901 C193.539891,123.290155 183.391518,135.09489 170.525237,135.09489 Z"
            fill="currentColor"
            fill-rule="nonzero"
          ></path>
        </svg>
      </div>
    </a>
    <a href="https://github.com/TheBluCoder" target="_blank" class="social-icon-link animate">
      <GithubIcon class="w-8 h-8" />
    </a>

    <div class="w-14 h-14 fixed bottom-10 left-32" v-show="!hide_waving_icon && $route.name == 'home'">
      <a href="https://www.animatedimages.org/cat-waving-1645.htm"
        ><img
          src="https://www.animatedimages.org/data/media/1645/animated-waving-image-0072.gif"
          border="0"
          alt="animated-waving-image-0072"
      /></a>
    </div>
  </div>
</template>

<script setup>
import { LinkedinIcon, MailIcon, MessageCircleIcon, GithubIcon } from 'lucide-vue-next'
import { ref } from 'vue'

defineEmits(['open-chat'])
const hide_waving_icon = ref(false)
</script>

<style scoped>
.social-icon-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  background: rgba(20, 20, 20, 0.7);
  border-radius: 50%;
  color: white;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(50, 50, 50, 0.5);
  opacity: 0;
  transform: scale(0.8);
}

.social-icon-link.animate {
  animation: socialIconPop 0.5s ease forwards;
  animation-delay: calc(var(--i, 0) * 0.1s);
}

.social-icon-link:nth-child(1) {
  --i: 1;
}
.social-icon-link:nth-child(2) {
  --i: 2;
}
.social-icon-link:nth-child(3) {
  --i: 3;
}
.social-icon-link:nth-child(4) {
  --i: 4;
}
.social-icon-link:nth-child(5) {
  --i: 5;
}

.social-icon-link:hover {
  background: rgba(40, 40, 40, 0.8);
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.4);
}

@keyframes socialIconPop {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
