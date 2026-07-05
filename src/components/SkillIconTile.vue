<script setup>
import { computed } from 'vue'
import { Icon } from '@iconify/vue'
import { Code2Icon } from 'lucide-vue-next'
import { resolveSkillIcon } from '@/lib/skillIcons'

const props = defineProps({
  skill: { type: [String, Object], required: true },
  compact: { type: Boolean, default: false },
  fallbackIcon: { type: Boolean, default: false },
})

const resolved = computed(() => resolveSkillIcon(props.skill))
</script>

<template>
  <div
    v-if="resolved.icon || resolved.fallbackIcon || fallbackIcon"
    class="skill-icon-tile"
    :class="{
      'skill-icon-tile--compact': compact,
      'skill-icon-tile--fallback': !resolved.icon,
    }"
  >
    <span class="skill-icon-frame">
      <Icon v-if="resolved.icon" :icon="resolved.icon" class="skill-icon" aria-hidden="true" />
      <i
        v-else-if="resolved.fallbackIcon"
        :class="resolved.fallbackIcon"
        class="skill-icon skill-icon--fallback"
        aria-hidden="true"
      ></i>
      <Code2Icon v-else class="skill-icon skill-icon--fallback" aria-hidden="true" />
    </span>
    <span class="skill-icon-label">{{ resolved.label }}</span>
  </div>
  <span v-else class="skill-text-fallback">{{ resolved.label }}</span>
</template>

<style scoped>
.skill-icon-tile {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 0.45rem;
  width: 4.9rem;
  min-height: 4.9rem;
  padding: 0.15rem 0.25rem;
  color: var(--theme-text-dim);
  cursor: default;
  transition:
    transform 0.15s ease,
    color 0.15s ease;
}

.skill-icon-tile:hover {
  transform: translateY(-2px);
  color: var(--theme-text);
}

.skill-icon-frame {
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
}

.skill-icon {
  width: 2rem;
  height: 2rem;
  color: inherit;
}

.skill-icon--fallback {
  color: var(--theme-accent-soft);
}

.skill-icon-label {
  width: 100%;
  color: inherit;
  font-size: 0.76rem;
  font-weight: 500;
  line-height: 1.2;
  text-align: center;
  overflow-wrap: anywhere;
}

.skill-icon-tile--compact {
  width: 4.5rem;
  min-height: 4.55rem;
}

.skill-icon-tile--compact .skill-icon-frame {
  width: 2.25rem;
  height: 2.25rem;
}

.skill-icon-tile--compact .skill-icon {
  width: 1.75rem;
  height: 1.75rem;
}

.skill-text-fallback {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  min-height: 1.75rem;
  padding: 0.3rem 0.8rem;
  border: 1px solid rgb(var(--theme-white-rgb) / 0.07);
  border-radius: 9999px;
  background: rgb(var(--theme-white-rgb) / 0.03);
  color: var(--theme-text-dim);
  font-size: 0.8125rem;
  line-height: 1.2;
  cursor: default;
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    color 0.15s ease;
}

.skill-text-fallback:hover {
  border-color: rgb(var(--theme-accent-rgb) / 0.22);
  background: rgb(var(--theme-accent-rgb) / 0.08);
  color: var(--theme-accent-soft);
}
</style>
