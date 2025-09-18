<template>
  <div class="project-detail-view">
    <ProjectDetailContainer
      :project-id="projectId"
      @back="router.push('/projects')"
    />
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'
import ProjectDetailContainer from '../components/project/ProjectDetailContainer.vue'

const route = useRoute()
const router = useRouter()

const projectId = computed(() => {
  const id = route.params.id
  return Array.isArray(id) ? parseInt(id[0]) : parseInt(id)
})
</script>

<style scoped>
.project-detail-view {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f5f5;
}

@media (max-width: 768px) {
  .project-detail-view {
    padding: 10px;
  }
}
</style>