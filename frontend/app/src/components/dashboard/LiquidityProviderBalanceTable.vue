<script setup lang="ts">
import { type BigNumber } from '@rotki/common';
import {
  type XswapAsset,
  type XswapBalance
} from '@rotki/common/lib/defi/xswap';
import isEqual from 'lodash/isEqual';
import { type Ref } from 'vue';
import { type DataTableHeader } from 'vuetify';
import { Routes } from '@/router/routes';
import {
  DashboardTableType,
  type DashboardTablesVisibleColumns
} from '@/types/frontend-settings';
import { Section } from '@/types/status';
import { TableColumn } from '@/types/table-column';

const { tc } = useI18n();
const LIQUIDITY_POSITION = DashboardTableType.LIQUIDITY_POSITION;

const createTableHeaders = (
  currency: Ref<string>,
  dashboardTablesVisibleColumns: Ref<DashboardTablesVisibleColumns>
) =>
  computed<DataTableHeader[]>(() => {
    const visibleColumns = get(dashboardTablesVisibleColumns)[
      LIQUIDITY_POSITION
    ];

    const headers: DataTableHeader[] = [
      {
        text: tc('common.name'),
        value: 'name',
        cellClass: 'text-no-wrap',
        sortable: false
      },
      {
        text: tc('common.value_in_symbol', 0, {
          symbol: get(currency)
        }),
        value: 'usdValue',
        align: 'end',
        class: 'text-no-wrap'
      }
    ];

    if (visibleColumns.includes(TableColumn.PERCENTAGE_OF_TOTAL_NET_VALUE)) {
      headers.push({
        text: tc('dashboard_asset_table.headers.percentage_of_total_net_value'),
        value: 'percentageOfTotalNetValue',
        align: 'end',
        class: 'text-no-wrap',
        sortable: false
      });
    }

    if (
      visibleColumns.includes(TableColumn.PERCENTAGE_OF_TOTAL_CURRENT_GROUP)
    ) {
      headers.push({
        text: tc(
          'dashboard_asset_table.headers.percentage_of_total_current_group',
          0,
          {
            group: tc('dashboard.liquidity_position.title')
          }
        ),
        value: 'percentageOfTotalCurrentGroup',
        align: 'end',
        class: 'text-no-wrap',
        sortable: false
      });
    }

    headers.push({ text: '', value: 'data-table-expand', sortable: false });

    return headers;
  });

const route = Routes.DEFI_DEPOSITS_LIQUIDITY;
const expanded = ref<XswapBalance[]>([]);

const {
  fetchV2Balances: fetchUniswapV2Balances,
  fetchV3Balances: fetchUniswapV3Balances
} = useUniswapStore();

const { fetchBalances: fetchSushiswapBalances } = useSushiswapStore();
const { fetchBalances: fetchBalancerBalances } = useBalancerStore();

const { lpAggregatedBalances, lpTotal, getPoolName } = useLiquidityPosition();
const balances = lpAggregatedBalances(true);
const totalInUsd = lpTotal(true);

const { currencySymbol } = storeToRefs(useGeneralSettingsStore());
const { dashboardTablesVisibleColumns } = storeToRefs(
  useFrontendSettingsStore()
);

const tableHeaders = createTableHeaders(
  currencySymbol,
  dashboardTablesVisibleColumns
);

const { isLoading } = useStatusStore();

const loading = logicOr(
  isLoading(Section.DEFI_UNISWAP_V3_BALANCES),
  isLoading(Section.DEFI_UNISWAP_V2_BALANCES),
  isLoading(Section.DEFI_BALANCER_BALANCES),
  isLoading(Section.DEFI_SUSHISWAP_BALANCES)
);

const statistics = useStatisticsStore();
const { totalNetWorthUsd } = storeToRefs(statistics);

const percentageOfTotalNetValue = (value: BigNumber) => {
  const netWorth = get(totalNetWorthUsd) as BigNumber;
  const total = netWorth.lt(0) ? get(totalInUsd) : netWorth;
  return calculatePercentage(value, total);
};

const percentageOfCurrentGroup = (value: BigNumber) =>
  calculatePercentage(value, get(totalInUsd));

const premium = usePremium();

const { ethAddresses } = storeToRefs(useEthAccountsStore());

const fetch = async (refresh = false) => {
  if (get(ethAddresses).length > 0) {
    await fetchUniswapV3Balances(refresh);
    await fetchUniswapV2Balances(refresh);

    if (get(premium)) {
      await fetchSushiswapBalances(refresh);
      await fetchBalancerBalances(refresh);
    }
  }
};

onBeforeMount(async () => {
  await fetch();
});

watch(ethAddresses, async (curr, prev) => {
  if (!isEqual(curr, prev)) {
    await fetch(true);
  }
});

watch(premium, async (curr, prev) => {
  if (prev !== curr) {
    await fetch(true);
  }
});

const getAssets = (assets: XswapAsset[]) => assets.map(({ asset }) => asset);
</script>

<template>
  <dashboard-expandable-table v-if="balances.length > 0 || loading">
    <template #title>
      <refresh-button
        :loading="loading"
        :tooltip="tc('dashboard.liquidity_position.refresh_tooltip')"
        @refresh="fetch(true)"
      />
      {{ tc('dashboard.liquidity_position.title') }}
      <v-btn :to="route" icon class="ml-2">
        <v-icon>mdi-chevron-right</v-icon>
      </v-btn>
    </template>
    <template #details>
      <v-menu
        id="nft_balance_table__column-filter"
        transition="slide-y-transition"
        max-width="250px"
        offset-y
      >
        <template #activator="{ on }">
          <menu-tooltip-button
            :tooltip="tc('dashboard_asset_table.select_visible_columns')"
            class-name="ml-4 nft_balance_table__column-filter__button"
            :on-menu="on"
          >
            <v-icon>mdi-dots-vertical</v-icon>
          </menu-tooltip-button>
        </template>
        <visible-columns-selector
          :group="LIQUIDITY_POSITION"
          :group-label="tc('dashboard.liquidity_position.title')"
        />
      </v-menu>
    </template>
    <template #shortDetails>
      <amount-display
        :value="totalInUsd"
        show-currency="symbol"
        fiat-currency="USD"
      />
    </template>
    <data-table
      :headers="tableHeaders"
      :items="balances"
      sort-by="userBalance.usdValue"
      :loading="loading"
      item-key="id"
      show-expand
      :expanded="expanded"
    >
      <template #item.name="{ item }">
        <div v-if="item.type === 'nft'">
          <nft-details
            :identifier="item.asset"
            :styled="{ margin: '1px 4px' }"
          />
        </div>

        <div v-else class="d-flex align-center py-4">
          <lp-pool-icon :type="item.lpType" :assets="getAssets(item.assets)" />
          <div class="pl-4 font-weight-medium">
            {{ getPoolName(item.lpType, getAssets(item.assets)) }}
          </div>
        </div>
      </template>
      <template #item.usdValue="{ item }">
        <amount-display :value="item.usdValue" fiat-currency="USD" />
      </template>
      <template #item.percentageOfTotalNetValue="{ item }">
        <percentage-display :value="percentageOfTotalNetValue(item.usdValue)" />
      </template>
      <template #item.percentageOfTotalCurrentGroup="{ item }">
        <percentage-display :value="percentageOfCurrentGroup(item.usdValue)" />
      </template>
      <template #expanded-item="{ headers, item }">
        <liquidity-provider-balance-details
          :span="headers.length"
          :assets="item.assets"
          :premium-only="item.premiumOnly"
        />
      </template>
      <template #body.append="{ isMobile }">
        <row-append
          label-colspan="1"
          :label="tc('common.total')"
          :right-patch-colspan="tableHeaders.length - 2"
          :is-mobile="isMobile"
        >
          <amount-display
            :value="totalInUsd"
            show-currency="symbol"
            fiat-currency="USD"
          />
        </row-append>
      </template>
    </data-table>
  </dashboard-expandable-table>
</template>
