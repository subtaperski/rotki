<script setup lang="ts">
import { type EthStakingPeriod } from '@rotki/common/lib/staking/eth2';
import { type ComputedRef } from 'vue';
import {
  type MatchedKeyword,
  type SearchMatcher,
  dateDeserializer,
  dateSerializer,
  dateValidator
} from '@/types/filtering';

enum Eth2StakingFilterKeys {
  START = 'start',
  END = 'end'
}

enum Eth2StakingFilterValueKeys {
  START = 'fromTimestamp',
  END = 'toTimestamp'
}

export type Matcher = SearchMatcher<
  Eth2StakingFilterKeys,
  Eth2StakingFilterValueKeys
>;
export type Filters = MatchedKeyword<Eth2StakingFilterValueKeys>;

const emit = defineEmits<{
  (e: 'update:period', value: EthStakingPeriod): void;
}>();

const filters: Ref<Filters> = ref({});

const { dateInputFormat } = storeToRefs(useFrontendSettingsStore());

const { tc } = useI18n();

const matchers: ComputedRef<Matcher[]> = computed(
  () =>
    [
      {
        key: Eth2StakingFilterKeys.START,
        keyValue: Eth2StakingFilterValueKeys.START,
        description: tc('closed_trades.filter.start_date'),
        string: true,
        suggestions: () => [],
        hint: tc('closed_trades.filter.date_hint', 0, {
          format: getDateInputISOFormat(get(dateInputFormat))
        }),
        validate: dateValidator(dateInputFormat),
        serializer: dateSerializer(dateInputFormat),
        deserializer: dateDeserializer(dateInputFormat)
      },
      {
        key: Eth2StakingFilterKeys.END,
        keyValue: Eth2StakingFilterValueKeys.END,
        description: tc('closed_trades.filter.end_date'),
        string: true,
        suggestions: () => [],
        hint: tc('closed_trades.filter.date_hint', 0, {
          format: getDateInputISOFormat(get(dateInputFormat))
        }),
        validate: dateValidator(dateInputFormat),
        serializer: dateSerializer(dateInputFormat),
        deserializer: dateDeserializer(dateInputFormat)
      }
    ] satisfies Matcher[]
);

const updateFilters = (updatedFilters: Filters) => {
  set(filters, updatedFilters);
  const { fromTimestamp, toTimestamp } = updatedFilters;
  assert(!Array.isArray(fromTimestamp));
  assert(!Array.isArray(toTimestamp));

  emit('update:period', { fromTimestamp, toTimestamp });
};
</script>

<template>
  <table-filter
    :matchers="matchers"
    :matches="filters"
    @update:matches="updateFilters($event)"
  />
</template>
