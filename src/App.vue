<template>
  <div>
    <Layout>
      <div>
        <HomeView v-show="!show_home_w_dir" class="w-full" @switch-view="show_home_w_dir = true" />
        <Introduction v-show="show_home_w_dir" />
      </div>
    </Layout>
    <!-- <home_w_directories v-show="show_home_w_dir" /> -->
  </div>
</template>

<script setup>
import Layout from './components/Layout.vue'
import HomeView from './views/HomeView.vue'
import Introduction from './views/Introduction.vue'
import { ref } from 'vue'

const show_home_w_dir = ref(false)
</script>

<style scoped></style>
