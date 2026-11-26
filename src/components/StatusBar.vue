<script setup>
defineProps({
  light: { type: Boolean, default: false }
})
</script>

<template>
  <header class="sb" :class="{ 'sb--light': light }" aria-hidden="true">
    <span class="sb__time num">9:41</span>
    <span class="sb__glyphs">
      <svg viewBox="0 0 18 12" width="17" height="11" fill="currentColor">
        <rect x="0" y="7.4" width="3" height="4.6" rx="1" />
        <rect x="4.8" y="5.2" width="3" height="6.8" rx="1" />
        <rect x="9.6" y="2.8" width="3" height="9.2" rx="1" />
        <rect x="14.4" y="0.4" width="3" height="11.6" rx="1" />
      </svg>
      <svg
        viewBox="0 0 16 12"
        width="16"
        height="12"
        fill="none"
        stroke="currentColor"
        stroke-width="1.7"
        stroke-linecap="round"
      >
        <path d="M1.1 4.3a10.4 10.4 0 0 1 13.8 0" />
        <path d="M3.8 7.1a6.2 6.2 0 0 1 8.4 0" />
        <path d="M6.5 9.8a2.5 2.5 0 0 1 3 0" />
      </svg>
      <svg viewBox="0 0 26 12" width="25" height="11">
        <rect
          x="0.6"
          y="0.6"
          width="21"
          height="10.8"
          rx="3.2"
          fill="none"
          stroke="currentColor"
          stroke-width="1.2"
          opacity="0.4"
        />
        <rect x="2.4" y="2.4" width="17.4" height="7.2" rx="2.1" fill="currentColor" />
        <rect x="22.8" y="3.9" width="2.2" height="4.2" rx="1.1" fill="currentColor" opacity="0.4" />
      </svg>
    </span>
  </header>
</template>

<style scoped>
.sb {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: var(--sb-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px 0 24px;
  color: var(--ink);
  z-index: 70;
  pointer-events: none;
  transition: color 0.3s ease;
}

.sb--light {
  color: var(--on-dark);
}

.sb__time {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.1px;
}

.sb__glyphs {
  display: flex;
  align-items: center;
  gap: 5px;
}
</style>
