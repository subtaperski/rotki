<script setup lang="ts">
const top = ref(0);
const proxy = useProxy();
onMounted(() => {
  const { top: topBound } = proxy.$el.getBoundingClientRect();
  set(top, topBound);
});
</script>

<template>
  <div
    class="d-flex flex-column align-center"
    :class="{
      [$style.empty]: true,
      'pa-2 mt-2': $vuetify.breakpoint.xsOnly
    }"
    :style="`height: calc(100vh - ${top + 64}px);`"
  >
    <slot />
  </div>
</template>

<style module lang="scss">
.empty {
  height: 100%;
}
</style>
