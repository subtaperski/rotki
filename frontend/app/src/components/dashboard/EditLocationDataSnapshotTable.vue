<script setup lang="ts">
import { type BigNumber } from '@rotki/common';
import { type PropType } from 'vue';
import { type DataTableHeader } from 'vuetify';
import { CURRENCY_USD } from '@/types/currencies';
import {
  type LocationDataSnapshot,
  type LocationDataSnapshotPayload
} from '@/types/snapshots';

type IndexedLocationDataSnapshot = LocationDataSnapshot & { index: number };

const props = defineProps({
  value: {
    required: true,
    type: Array as PropType<LocationDataSnapshot[]>
  },
  timestamp: {
    required: true,
    type: Number
  }
});

const emit = defineEmits<{
  (e: 'update:step', step: number): void;
  (e: 'input', value: LocationDataSnapshot[]): void;
}>();

const { value, timestamp } = toRefs(props);
const { currencySymbol } = storeToRefs(useGeneralSettingsStore());
const showForm = ref<boolean>(false);
const editedIndex = ref<number | null>(null);
const form = ref<LocationDataSnapshotPayload | null>(null);
const valid = ref<boolean>(false);
const loading = ref<boolean>(false);
const excludedLocations = ref<string[]>([]);

const { tc } = useI18n();

const tableHeaders = computed<DataTableHeader[]>(() => [
  {
    text: tc('common.location'),
    value: 'location',
    cellClass: 'py-2',
    width: 200,
    align: 'center'
  },
  {
    text: tc('common.value_in_symbol', 0, {
      symbol: get(currencySymbol)
    }),
    value: 'usdValue',
    align: 'end',
    sort: (a: BigNumber, b: BigNumber) => sortDesc(a, b)
  },
  {
    text: '',
    value: 'action',
    cellClass: 'py-2',
    width: 100,
    sortable: false
  }
]);

const { exchangeRate } = useBalancePricesStore();
const fiatExchangeRate = computed<BigNumber>(
  () => get(exchangeRate(get(currencySymbol))) ?? One
);

const data = computed<IndexedLocationDataSnapshot[]>(() =>
  get(value)
    .map((item, index) => ({ ...item, index }))
    .filter(item => item.location !== 'total')
);

const input = (value: LocationDataSnapshot[]) => {
  emit('input', value);
};

const updateStep = (step: number) => {
  emit('update:step', step);
};

const editClick = (item: IndexedLocationDataSnapshot) => {
  set(editedIndex, item.index);

  const convertedFiatValue =
    get(currencySymbol) === CURRENCY_USD
      ? item.usdValue.toFixed()
      : item.usdValue.multipliedBy(get(fiatExchangeRate)).toFixed();

  set(form, {
    ...item,
    usdValue: convertedFiatValue
  });

  set(
    excludedLocations,
    get(value)
      .map(item => item.location)
      .filter(identifier => identifier !== item.location)
  );

  set(showForm, true);
};

const add = () => {
  set(editedIndex, null);
  set(form, {
    timestamp: get(timestamp),
    location: '',
    usdValue: ''
  });
  set(
    excludedLocations,
    get(value).map(item => item.location)
  );
  set(showForm, true);
};

const save = () => {
  const formVal = get(form);

  if (!formVal) {
    return;
  }

  const index = get(editedIndex);
  const val = get(value);
  const timestampVal = get(timestamp);

  const convertedUsdValue =
    get(currencySymbol) === CURRENCY_USD
      ? bigNumberify(formVal.usdValue)
      : bigNumberify(formVal.usdValue).dividedBy(get(fiatExchangeRate));

  const newValue = [...val];
  const payload = {
    timestamp: timestampVal,
    location: formVal.location,
    usdValue: convertedUsdValue
  };

  if (index !== null) {
    newValue[index] = payload;
  } else {
    newValue.unshift(payload);
  }

  input(newValue);
  clearEditDialog();
};

const clearEditDialog = () => {
  set(editedIndex, null);
  set(showForm, false);
  set(form, null);
  set(excludedLocations, []);
};

const updateForm = (newForm: LocationDataSnapshotPayload) => {
  set(form, newForm);
};

const confirmDelete = (index: number) => {
  const val = get(value);

  if (index === null) {
    return;
  }

  const newValue = [...val];
  newValue.splice(index, 1);

  input(newValue);
};

const total = computed<BigNumber>(() => {
  const totalEntry = get(value).find(item => item.location === 'total');

  if (!totalEntry) {
    return Zero;
  }
  return totalEntry.usdValue;
});

const { show } = useConfirmStore();

const showDeleteConfirmation = (item: IndexedLocationDataSnapshot) => {
  show(
    {
      title: tc('dashboard.snapshot.edit.dialog.location_data.delete_title'),
      message: tc(
        'dashboard.snapshot.edit.dialog.location_data.delete_confirmation'
      )
    },
    () => confirmDelete(item.index)
  );
};
</script>

<template>
  <div>
    <data-table
      class="table-inside-dialog"
      :headers="tableHeaders"
      :items="data"
      :mobile-breakpoint="0"
    >
      <template #item.location="{ item }">
        <location-display :opens-details="false" :identifier="item.location" />
      </template>

      <template #item.usdValue="{ item }">
        <amount-display :value="item.usdValue" fiat-currency="USD" />
      </template>

      <template #item.action="{ item }">
        <row-actions
          :edit-tooltip="tc('dashboard.snapshot.edit.dialog.actions.edit_item')"
          :delete-tooltip="
            tc('dashboard.snapshot.edit.dialog.actions.delete_item')
          "
          @edit-click="editClick(item)"
          @delete-click="showDeleteConfirmation(item)"
        />
      </template>
    </data-table>
    <v-sheet elevation="10" class="d-flex align-center px-4 py-2">
      <div>
        <div class="text-caption">{{ tc('common.total') }}:</div>
        <div class="font-weight-bold text-h6 mt-n1">
          <amount-display :value="total" fiat-currency="USD" />
        </div>
      </div>
      <v-spacer />
      <v-btn text color="primary" class="mr-4" @click="add()">
        <v-icon class="mr-2">mdi-plus</v-icon>
        <span>
          {{ tc('dashboard.snapshot.edit.dialog.actions.add_new_entry') }}
        </span>
      </v-btn>
      <v-btn class="mr-4" @click="updateStep(1)">
        <v-icon>mdi-chevron-left</v-icon>
        {{ tc('common.actions.back') }}
      </v-btn>
      <v-btn color="primary" @click="updateStep(3)">
        {{ tc('common.actions.next') }}
        <v-icon>mdi-chevron-right</v-icon>
      </v-btn>
    </v-sheet>

    <big-dialog
      :display="showForm"
      :title="
        editedIndex !== null
          ? tc('dashboard.snapshot.edit.dialog.location_data.edit_title')
          : tc('dashboard.snapshot.edit.dialog.location_data.add_title')
      "
      :primary-action="tc('common.actions.save')"
      :action-disabled="loading || !valid"
      @confirm="save()"
      @cancel="clearEditDialog()"
    >
      <edit-location-data-snapshot-form
        v-if="form"
        v-model="valid"
        :form="form"
        :excluded-locations="excludedLocations"
        @update:form="updateForm($event)"
      />
    </big-dialog>
  </div>
</template>

<style module lang="scss">
.asset {
  max-width: 640px;
}
</style>
