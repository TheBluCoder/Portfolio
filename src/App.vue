<template>
  <div>
    <Layout>
      <div>
        <Home v-show="!show_home_w_dir" class="w-full" @switch-view="show_home_w_dir = true" />
        <Introduction v-show="show_home_w_dir" />
      </div>
    </Layout>
    <!-- <home_w_directories v-show="show_home_w_dir" /> -->
  </div>
</template>

<script setup>
import Layout from './components/Layout.vue'
import Home from './components/Home.vue'
import Home_w_directories from '@/components/Home_w_directories.vue'
import Introduction from './components/Introduction.vue'
import { ref } from 'vue'

const show_home_w_dir = ref(false)
</script>

<style scoped></style>
