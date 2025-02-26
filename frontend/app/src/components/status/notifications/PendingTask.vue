<script setup lang="ts">
import dayjs from 'dayjs';
import { type Task, type TaskMeta } from '@/types/task';
import { TaskType } from '@/types/task-type';

const props = defineProps<{ task: Task<TaskMeta> }>();

const css = useCssModule();

const { task } = toRefs(props);
const isHistory = computed(() => task.value.type === TaskType.TRADE_HISTORY);

const { progress } = storeToRefs(useReportsStore());

const time = computed(() => dayjs(task.value.time).format('LLL'));
</script>

<template>
  <card outlined :class="css.task">
    <v-row align="center" no-gutters class="flex-nowrap">
      <v-col>
        <v-row no-gutters>
          <v-col>
            <div :class="css.title" class="text--primary">
              {{ task.meta.title }}
            </div>
          </v-col>
        </v-row>
        <v-row
          v-if="task.meta.description"
          no-gutters
          :class="css.description"
          class="text--secondary"
        >
          {{ task.meta.description }}
        </v-row>
        <v-row class="text-caption px-3" :class="css.date">
          {{ time }}
        </v-row>
      </v-col>
      <v-col cols="auto">
        <v-progress-circular
          v-if="isHistory"
          size="20"
          width="2"
          :value="progress"
          color="primary"
        />
        <v-icon v-else color="primary">mdi-spin mdi-loading</v-icon>
      </v-col>
    </v-row>
  </card>
</template>

<style module lang="scss">
.task {
  margin: 6px 0;
}

.title {
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.description {
  font-size: 0.8rem;
  white-space: pre-line;
}

.date {
  font-size: 0.75rem;
}
</style>
