<template>
  <div class="loading-overlay">
    <div class="glass-background"></div>
    <div class="animation-container">
      <div class="logo-bounce">
        <svg width="100" height="100" viewBox="0 0 24 24" fill="#1565FF" xmlns="http://www.w3.org/2000/svg" class="spotify-logo">
          <path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.49 17.29c-.22.35-.67.46-1.02.24-2.84-1.74-6.42-2.13-10.63-1.18-.4.09-.79-.16-.88-.55-.09-.4.16-.79.55-.88 4.62-1.05 8.58-.6 11.75 1.34.34.22.45.67.23 1.03zm1.46-3.26c-.27.44-.85.59-1.3.31-3.25-1.99-8.2-2.58-12.04-1.41-.5.15-1.02-.13-1.17-.63-.15-.5.13-1.02.63-1.17 4.41-1.34 9.87-.67 13.57 1.6.45.27.6.85.31 1.3zm.14-3.41c-3.9-2.31-10.32-2.53-14.07-1.39-.6.18-1.24-.16-1.42-.76-.18-.6.16-1.24.76-1.42 4.31-1.31 11.41-1.05 15.93 1.63.54.32.72 1.02.4 1.56-.32.54-1.02.72-1.6.4z"/>
        </svg>
        <div class="logo-glow"></div>
      </div>
      <div class="text-bounce">
        <span class="insight-text">INSIGHTS</span>
        <div class="reflection">INSIGHTS</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: black;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  overflow: hidden;
}

.glass-background {
    position: absolute;
    width: 150%; height: 150%;
    background: radial-gradient(circle at center, rgba(21, 101, 255, 0.15) 0%, transparent 60%);
    filter: blur(80px);
    animation: rotate-bg 15s linear infinite;
}

@keyframes rotate-bg {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.animation-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  position: relative;
  z-index: 10;
}

.logo-bounce {
    position: relative;
    animation: spotify-bounce 2s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite;
}

.spotify-logo {
    filter: drop-shadow(0 0 30px rgba(21, 101, 255, 0.5));
}

.logo-glow {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 120px; height: 120px;
    background: var(--spotify-green);
    filter: blur(40px);
    opacity: 0.4;
    border-radius: 50%;
    animation: glow-pulse 2s infinite;
}

.text-bounce {
    display: flex;
    flex-direction: column;
    align-items: center;
    animation: text-float 2s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite;
    animation-delay: 0.2s;
}

.insight-text {
    font-size: 1.5rem;
    font-weight: 900;
    letter-spacing: 8px;
    color: white;
    text-transform: uppercase;
    text-shadow: 0 0 20px rgba(255,255,255,0.3);
}

.reflection {
    font-size: 1.5rem;
    font-weight: 900;
    letter-spacing: 8px;
    color: rgba(255,255,255,0.1);
    transform: scaleY(-1) translateY(-10px);
    filter: blur(2px);
}

@keyframes spotify-bounce {
    0%, 100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-30px) scale(1.05); }
}

@keyframes text-float {
    0%, 100% { transform: translateY(0); opacity: 0.6; }
    50% { transform: translateY(-10px); opacity: 1; }
}

@keyframes glow-pulse {
    0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.4; }
    50% { transform: translate(-50%, -50%) scale(1.4); opacity: 0.6; }
}

@media (max-width: 768px) {
    .spotify-logo { width: 80px; height: 80px; }
    .insight-text, .reflection { font-size: 1.1rem; letter-spacing: 5px; }
}
</style>
