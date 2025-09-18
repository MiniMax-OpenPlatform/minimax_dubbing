<template>
  <ProjectDetailContainer
    :project-id="projectId"
    @back="emit('back')"
  />
</template>

<script setup lang="ts">
import ProjectDetailContainer from './project/ProjectDetailContainer.vue'

const props = defineProps<{
  projectId: number
}>()

const emit = defineEmits<{
  back: []
}>()
</script>