<script setup lang="ts">
import { ChevronUp } from 'lucide-vue-next'
defineProps<{
  title: string
  value: number | string
  percent?: number
  icon: any
  color: string
}>()
</script>

<template>
  <div class="stat-card-nebula glass">
    <div class="card-glow" :style="{ background: color }"></div>
    
    <div class="card-header">
      <div class="icon-orb" :style="{ color: color, borderColor: color + '33' }">
        <component :is="icon" :size="20" />
      </div>
      <div class="header-text">
          <span class="label">{{ title }}</span>
          <span class="biometric-tag">BIOMETRÍA OK</span>
      </div>
    </div>
    
    <div class="card-body">
      <span class="value">{{ value }}</span>
      <div v-if="percent !== undefined" class="mini-chart">
        <div class="track">
          <div class="bar" :style="{ width: percent + '%', background: `linear-gradient(90deg, ${color}, white)` }"></div>
        </div>
      </div>
    </div>
    
    <div class="card-footer">
        <div class="trend-badge">
            <ChevronUp :size="12" />
            <span>+{{ Math.floor(Math.random() * 8) + 1 }}% DESVIACIÓN</span>
        </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card-nebula {
  padding: 24px;
  border-radius: 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  overflow: hidden;
  cursor: default;
}

.stat-card-nebula:hover {
  transform: translateY(-8px) scale(1.02);
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.15);
}

.card-glow {
    position: absolute;
    top: -40px; right: -40px;
    width: 100px; height: 100px;
    filter: blur(40px);
    opacity: 0.15;
    z-index: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  z-index: 10;
}

.icon-orb {
  width: 44px;
  height: 44px;
  background: rgba(0,0,0,0.2);
  border: 1px solid transparent;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 10px rgba(0,0,0,0.2);
}

.header-text { display: flex; flex-direction: column; gap: 2px; }

.label {
  color: white;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: -0.2px;
}

.biometric-tag {
    font-size: 0.6rem;
    font-weight: 800;
    letter-spacing: 1px;
    color: var(--nebula-text-muted);
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
  z-index: 10;
}

.value {
  font-size: 2.8rem;
  font-weight: 800;
  letter-spacing: -2px;
  color: white;
}

.mini-chart { width: 100%; }

.track {
    height: 4px;
    background: rgba(255,255,255,0.04);
    border-radius: 10px;
    overflow: hidden;
}

.bar {
    height: 100%;
    border-radius: 10px;
    transition: width 1.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.card-footer {
    display: flex;
    align-items: center;
    position: relative;
    z-index: 10;
}

.trend-badge {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.7rem;
    color: var(--nebula-accent);
    font-weight: 800;
    letter-spacing: 1px;
    background: rgba(34, 211, 238, 0.08);
    padding: 4px 10px;
    border-radius: 500px;
}
</style>
