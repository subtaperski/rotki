﻿<script setup lang="ts">
import { Blockchain } from '@rotki/common/lib/blockchain';
import { truncateAddress } from '@/filters';
import {
  type Chains,
  type ExplorerUrls,
  explorerUrls
} from '@/types/asset/asset-urls';

const props = withDefaults(
  defineProps<{
    showIcon?: boolean;
    text?: string;
    fullAddress?: boolean;
    linkOnly?: boolean;
    noLink?: boolean;
    baseUrl?: string;
    chain?: Chains;
    tx?: boolean;
    buttons?: boolean;
    small?: boolean;
    truncateLength?: number;
    type?: keyof ExplorerUrls;
  }>(),
  {
    showIcon: true,
    text: '',
    fullAddress: false,
    linkOnly: false,
    noLink: false,
    baseUrl: '',
    chain: Blockchain.ETH,
    tx: false,
    buttons: false,
    small: false,
    truncateLength: 4,
    type: 'address'
  }
);

const { text, baseUrl, chain, type } = toRefs(props);
const { scrambleData, shouldShowAmount, scrambleHex } = useScramble();

const { explorers } = storeToRefs(useFrontendSettingsStore());
const { dark } = useTheme();

const { addressNameSelector } = useAddressesNamesStore();

const aliasName = computed<string | null>(() => {
  if (get(scrambleData) || get(type) !== 'address') {
    return null;
  }

  return get(addressNameSelector(text, chain));
});

const displayText = computed<string>(() => {
  const textVal = get(text);
  return scrambleHex(textVal);
});

const base = computed<string>(() => {
  if (get(baseUrl)) {
    return get(baseUrl);
  }

  const defaultSetting: ExplorerUrls = explorerUrls[get(chain)];
  let formattedBaseUrl: string | undefined = undefined;
  const typeVal = get(type);

  if (get(chain) === 'zksync') {
    formattedBaseUrl = defaultSetting[typeVal];
  } else {
    const explorersSetting =
      get(explorers)[get(chain) as Exclude<Chains, 'zksync'>];

    if (explorersSetting || defaultSetting) {
      formattedBaseUrl = explorersSetting?.[typeVal] ?? defaultSetting[typeVal];
    }
  }

  if (!formattedBaseUrl) {
    return '';
  }

  return formattedBaseUrl.endsWith('/')
    ? formattedBaseUrl
    : `${formattedBaseUrl}/`;
});

const copyText = async (text: string) => {
  const { copy } = useClipboard({ source: text });
  await copy();
};

const url = computed<string>(() => get(base) + get(text));

const displayUrl = computed<string>(
  () => get(base) + truncateAddress(get(text), 10)
);

const { t } = useI18n();
const { href, onLinkClick } = useLinks(url);
</script>

<template>
  <div class="d-flex flex-row shrink align-center">
    <span>
      <v-avatar v-if="showIcon && type === 'address'" size="22" class="mr-2">
        <ens-avatar :address="displayText" />
      </v-avatar>
    </span>
    <span v-if="!linkOnly && !buttons">
      <span v-if="fullAddress" :class="{ 'blur-content': !shouldShowAmount }">
        {{ displayText }}
      </span>
      <v-tooltip v-else top open-delay="400">
        <template #activator="{ on, attrs }">
          <span
            :class="{ 'blur-content': !shouldShowAmount }"
            v-bind="attrs"
            v-on="on"
          >
            <span v-if="aliasName">{{ aliasName }}</span>
            <span v-else>
              {{ truncateAddress(displayText, truncateLength) }}
            </span>
          </span>
        </template>
        <span> {{ displayText }} </span>
      </v-tooltip>
    </span>
    <v-tooltip v-if="!linkOnly || buttons" top open-delay="600">
      <template #activator="{ on, attrs }">
        <v-btn
          :x-small="!small"
          :small="small"
          icon
          v-bind="attrs"
          :width="!small ? '20px' : null"
          color="primary"
          class="ml-2"
          :class="dark ? null : 'grey lighten-4'"
          v-on="on"
          @click="copyText(text)"
        >
          <v-icon :x-small="!small" :small="small"> mdi-content-copy </v-icon>
        </v-btn>
      </template>
      <span>{{ t('common.actions.copy') }}</span>
    </v-tooltip>
    <v-tooltip v-if="!noLink || buttons" top open-delay="600">
      <template #activator="{ on, attrs }">
        <v-btn
          v-if="!!base"
          :x-small="!small"
          :small="small"
          icon
          v-bind="attrs"
          :width="!small ? '20px' : null"
          color="primary"
          class="ml-1"
          :class="dark ? null : 'grey lighten-4'"
          :href="href"
          target="_blank"
          v-on="on"
          @click="onLinkClick()"
        >
          <v-icon :x-small="!small" :small="small"> mdi-launch </v-icon>
        </v-btn>
      </template>
      <div>
        <div>{{ t('hash_link.open_link') }}:</div>
        <div>{{ displayUrl }}</div>
      </div>
    </v-tooltip>
  </div>
</template>

<style scoped lang="scss">
.blur-content {
  filter: blur(0.3em);
}
</style>
