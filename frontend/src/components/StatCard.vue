<script setup lang="ts">
defineProps<{
  title: string
  value: number | string
  percent?: number
  icon: any
  color: string
}>()
</script>

<template>
  <div class="stat-card-2026">
    <div class="card-header">
      <div class="icon-orb" :style="{ '--glow': color }">
        <component :is="icon" :size="20" />
      </div>
      <span class="label">{{ title }}</span>
    </div>
    
    <div class="card-body">
      <span class="value">{{ value }}</span>
      <div v-if="percent !== undefined" class="mini-chart">
        <div class="track">
          <div class="bar" :style="{ width: percent + '%', background: color }"></div>
        </div>
      </div>
    </div>
    
    <div class="card-footer">
        <span class="trend">↑ {{ Math.floor(Math.random() * 12) + 2 }}% coincidencia</span>
    </div>
  </div>
</template>

<style scoped>
.stat-card-2026 {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(10px);
  padding: 24px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  gap: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card-2026:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-5px);
  border-color: rgba(255, 255, 255, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-orb {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--glow);
  box-shadow: 0 0 20px rgba(0,0,0,0.2);
}

.label {
  color: var(--spotify-text-grey);
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.value {
  font-size: 2.5rem;
  font-weight: 900;
  letter-spacing: -1px;
}

.mini-chart {
    width: 100%;
}

.track {
    height: 6px;
    background: rgba(255,255,255,0.05);
    border-radius: 3px;
    overflow: hidden;
}

.bar {
    height: 100%;
    border-radius: 3px;
    transition: width 1.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.card-footer {
    display: flex;
    align-items: center;
}

.trend {
    font-size: 0.75rem;
    color: var(--spotify-green);
    font-weight: 700;
}
</style>
