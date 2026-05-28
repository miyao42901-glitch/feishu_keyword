<template>
  <router-view />
</template>

<script setup lang="ts"></script>

<style>
html,
body,
#app {
  margin: 0;
  height: 100%;
}

@media (max-width: 899px) {
  html {
    padding-left: env(safe-area-inset-left);
    padding-right: env(safe-area-inset-right);
  }
}
</style>
