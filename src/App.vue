<template>
  <div class="h-full">
    <Layout>
      <div class="h-full w-full">
        <router-view class="w-full h-full" @switch-view="switch_to_introduction($event)"></router-view>
      </div>
    </Layout>
  </div>
</template>

<script setup>
import Layout from './components/Layout.vue'
import router from './router'

const switch_to_introduction = (view)=>{
  router.push(`/${view}`)
}
</script>

<style scoped></style>
