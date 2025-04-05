<script setup>
import { onMounted } from 'vue'
import { FolderOpen } from 'lucide-vue-next'
const imgUrl = new URL('../assets/images/ubuntu.png', import.meta.url).href

onMounted(() => {
  const container = document.getElementById('ubuntu-container')
  container.style.backgroundImage = `url(${imgUrl})`
})
</script>

<template>
  <section>
    <div id="ubuntu-container"></div>
  </section>
</template>

<style scoped></style>
