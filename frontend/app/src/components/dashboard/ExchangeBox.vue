<script setup lang="ts">
import { BigNumber } from '@rotki/common';
import { type PropType } from 'vue';
import { type TradeLocation } from '@/types/history/trade/location';

defineProps({
  location: { required: true, type: String as PropType<TradeLocation> },
  amount: { required: true, type: BigNumber }
});

const { exchangeName } = useLocations();
</script>

<template>
  <v-list-item
    :id="`${location}_box`"
    :to="`/accounts-balances/exchange-balances/${location}`"
    :ripple="false"
    class="exchange-box__item"
  >
    <v-list-item-avatar tile class="exchange-box__icon">
      <location-display :identifier="location" icon />
    </v-list-item-avatar>
    <v-list-item-content>
      <v-list-item-title class="d-flex justify-space-between">
        <span>
          {{ exchangeName(location) }}
        </span>
        <span class="text-end">
          <amount-display
            show-currency="symbol"
            fiat-currency="USD"
            :value="amount"
          />
        </span>
      </v-list-item-title>
    </v-list-item-content>
  </v-list-item>
</template>

<style scoped lang="scss">
.exchange-box {
  &__icon {
    filter: grayscale(100%);
    margin: 0;
    margin-right: 5px !important;
  }

  &__item:hover &__icon {
    filter: grayscale(0);
  }
}
</style>
