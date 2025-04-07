<template>
  <div class="h-full">
    <Layout>
      <div class="h-full w-full">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" @switch-view="switch_view($event)" />
          </transition>
        </router-view>
      </div>
    </Layout>
  </div>
</template>

<script setup>
import Layout from './components/Layout.vue'
import router from './router'

const switch_view = (view) => {
  router.push(`/${view}`)
}
</script>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: all 0.5s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(100px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-100px);
}
</style>
