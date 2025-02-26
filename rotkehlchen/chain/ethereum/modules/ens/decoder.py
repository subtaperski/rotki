import logging
from multiprocessing.managers import RemoteError
from typing import TYPE_CHECKING, Any, Optional

from eth_utils import to_checksum_address

from rotkehlchen.accounting.structures.balance import Balance
from rotkehlchen.accounting.structures.types import HistoryEventSubType, HistoryEventType
from rotkehlchen.chain.ethereum.abi import decode_event_data_abi_str
from rotkehlchen.chain.evm.decoding.interfaces import DecoderInterface
from rotkehlchen.chain.evm.decoding.structures import (
    DEFAULT_DECODING_OUTPUT,
    DecoderContext,
    DecodingOutput,
)
from rotkehlchen.chain.evm.decoding.types import CounterpartyDetails, EventCategory
from rotkehlchen.chain.evm.names import find_ens_mappings
from rotkehlchen.chain.evm.types import string_to_evm_address
from rotkehlchen.constants.assets import A_ETH
from rotkehlchen.constants.misc import ZERO
from rotkehlchen.errors.serialization import DeserializationError
from rotkehlchen.logging import RotkehlchenLogsAdapter
from rotkehlchen.types import ChecksumEvmAddress, DecoderEventMappingType
from rotkehlchen.utils.misc import from_wei
from rotkehlchen.utils.mixins.customizable_date import CustomizableDateMixin

from .constants import CPT_ENS

if TYPE_CHECKING:
    from rotkehlchen.chain.ethereum.node_inquirer import EthereumInquirer
    from rotkehlchen.chain.evm.decoding.base import BaseDecoderTools
    from rotkehlchen.user_messages import MessagesAggregator


logger = logging.getLogger(__name__)
log = RotkehlchenLogsAdapter(logger)


ENS_REGISTRAR_CONTROLLER_1 = string_to_evm_address('0x283Af0B28c62C092C9727F1Ee09c02CA627EB7F5')
ENS_REGISTRAR_CONTROLLER_2 = string_to_evm_address('0x253553366Da8546fC250F225fe3d25d0C782303b')
ENS_REGISTRY_WITH_FALLBACK = string_to_evm_address('0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e')
ENS_PUBLIC_RESOLVER_2_ADDRESS = string_to_evm_address('0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41')
ENS_PUBLIC_RESOLVER_3_ADDRESS = string_to_evm_address('0x231b0Ee14048e9dCcD1d247744d114a4EB5E8E63')

NAME_RENEWED = b'=\xa2L\x02E\x82\x93\x1c\xfa\xf8&}\x8e\xd2M\x13\xa8*\x80h\xd5\xbd3}0\xecE\xce\xa4\xe5\x06\xae'  # noqa: E501
NAME_RENEWED_ABI = '{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"name","type":"string"},{"indexed":true,"internalType":"bytes32","name":"label","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"cost","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"expires","type":"uint256"}],"name":"NameRenewed","type":"event"}'  # noqa: E501
NEW_RESOLVER = b'3W!\xb0\x18f\xdc#\xfb\xee\x8bk,{\x1e\x14\xd6\xf0\\(\xcd5\xa2\xc94#\x9f\x94\tV\x02\xa0'  # noqa: E501
NAME_REGISTERED_SINGLE_COST = b'\xcaj\xbb\xe9\xd7\xf1\x14"\xcbl\xa7b\x9f\xbfo\xe9\xef\xb1\xc6!\xf7\x1c\xe8\xf0+\x9f*#\x00\x97@O'  # noqa: E501
NAME_REGISTERED_SINGLE_COST_ABI = '{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"name","type":"string"},{"indexed":true,"internalType":"bytes32","name":"label","type":"bytes32"},{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"uint256","name":"cost","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"expires","type":"uint256"}],"name":"NameRegistered","type":"event"}'  # noqa: E501
NAME_REGISTERED_BASE_COST_AND_PREMIUM = b"i\xe3\x7f\x15\x1e\xb9\x8a\ta\x8d\xda\xa8\x0c\x8c\xfa\xf1\xceY\x96\x86|H\x9fE\xb5U\xb4\x12'\x1e\xbf'"  # noqa: E501
NAME_REGISTERED_BASE_COST_AND_PREMIUM_ABI = '{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"name","type":"string"},{"indexed":true,"internalType":"bytes32","name":"label","type":"bytes32"},{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":false,"internalType":"uint256","name":"baseCost","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"premium","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"expires","type":"uint256"}],"name":"NameRegistered","type":"event"}'  # noqa: E501
TEXT_CHANGED_KEY_ONLY = b'\xd8\xc93K\x1a\x9c/\x9d\xa3B\xa0\xa2\xb3&)\xc1\xa2)\xb6D]\xadx\x94\x7fgKDDJuP'  # noqa: E501
TEXT_CHANGED_KEY_ONLY_ABI = '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"node","type":"bytes32"},{"indexed":true,"internalType":"string","name":"indexedKey","type":"string"},{"indexed":false,"internalType":"string","name":"key","type":"string"}],"name":"TextChanged","type":"event"}'  # noqa: E501
TEXT_CHANGED_KEY_AND_VALUE = b'D\x8b\xc0\x14\xf1Sg&\xcf\x8dT\xff=d\x81\xed<\xbch<%\x91\xca Bt\x00\x9a\xfa\t\xb1\xa1'  # noqa: E501
TEXT_CHANGED_KEY_AND_VALUE_ABI = '{"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"node","type":"bytes32"},{"indexed":true,"internalType":"string","name":"indexedKey","type":"string"},{"indexed":false,"internalType":"string","name":"key","type":"string"},{"indexed":false,"internalType":"string","name":"value","type":"string"}],"name":"TextChanged","type":"event"}'  # noqa: E501


class EnsDecoder(DecoderInterface, CustomizableDateMixin):
    def __init__(  # pylint: disable=super-init-not-called
            self,
            ethereum_inquirer: 'EthereumInquirer',
            base_tools: 'BaseDecoderTools',
            msg_aggregator: 'MessagesAggregator',  # pylint: disable=unused-argument
    ) -> None:
        super().__init__(
            evm_inquirer=ethereum_inquirer,
            base_tools=base_tools,
            msg_aggregator=msg_aggregator,
        )
        self.base = base_tools
        self.ethereum = ethereum_inquirer
        CustomizableDateMixin.__init__(self, base_tools.database)
        self.eth = A_ETH.resolve_to_crypto_asset()

    def _decode_ens_registrar_event(self, context: DecoderContext) -> DecodingOutput:
        if context.tx_log.topics[0] in (
            NAME_REGISTERED_SINGLE_COST,
            NAME_REGISTERED_BASE_COST_AND_PREMIUM,
        ):
            return self._decode_name_registered(context=context)

        if context.tx_log.topics[0] == NAME_RENEWED:
            return self._decode_name_renewed(context=context)

        return DEFAULT_DECODING_OUTPUT

    def _decode_name_registered(self, context: DecoderContext) -> DecodingOutput:
        try:
            _, decoded_data = decode_event_data_abi_str(
                context.tx_log,
                NAME_REGISTERED_SINGLE_COST_ABI if context.tx_log.topics[0] == NAME_REGISTERED_SINGLE_COST else NAME_REGISTERED_BASE_COST_AND_PREMIUM_ABI,  # noqa: E501
            )
        except DeserializationError as e:
            log.debug(f'Failed to decode ENS name registered event due to {e!s}')
            return DEFAULT_DECODING_OUTPUT

        name = decoded_data[0]
        if context.tx_log.topics[0] == NAME_REGISTERED_SINGLE_COST:
            amount = from_wei(decoded_data[1])
            expires = decoded_data[2]
        else:
            amount = from_wei(decoded_data[1] + decoded_data[2])  # In the new version the amount is baseCost + premium  # noqa: E501
            expires = decoded_data[3]

        refund_from_registrar = None
        to_remove_indices = []
        new_event = None
        for event_idx, event in enumerate(context.decoded_events):
            if event.event_type == HistoryEventType.RECEIVE and event.asset == A_ETH and event.address == ENS_REGISTRAR_CONTROLLER_1:  # noqa: E501
                # remove ETH refund event
                refund_from_registrar = event.balance.amount
                to_remove_indices.append(event_idx)

            # Find the ETH transfer event which should be before the registered event
            if event.event_type == HistoryEventType.SPEND and event.asset == A_ETH and event.address == context.tx_log.address:  # noqa: E501
                expected_amount = amount
                if refund_from_registrar:
                    expected_amount = amount + refund_from_registrar
                if event.balance.amount != expected_amount:
                    return DEFAULT_DECODING_OUTPUT  # registration amount did not match

                event.event_type = HistoryEventType.TRADE
                event.event_subtype = HistoryEventSubType.SPEND
                event.counterparty = CPT_ENS
                event.notes = f'Register ENS name {name}.eth for {amount} ETH until {self.timestamp_to_date(expires)}'  # noqa: E501

            # Find the ENS ERC721 receive event which should be before the registered event
            if event.event_type == HistoryEventType.RECEIVE and event.asset.identifier == 'eip155:1/erc721:0x57f1887a8BF19b14fC0dF6Fd9B2acc9Af147eA85':  # noqa: E501
                assert event.extra_data is not None, 'All ERC721 events should have extra data'
                event.event_type = HistoryEventType.TRADE
                event.event_subtype = HistoryEventSubType.RECEIVE
                event.counterparty = CPT_ENS
                event.notes = f'Receive ENS name ERC721 token for {name}.eth with id {event.extra_data["token_id"]}'  # noqa: E501

        for index in to_remove_indices:
            del context.decoded_events[index]

        return DecodingOutput(event=new_event)

    def _decode_name_renewed(self, context: DecoderContext) -> DecodingOutput:
        try:
            _, decoded_data = decode_event_data_abi_str(context.tx_log, NAME_RENEWED_ABI)
        except DeserializationError as e:
            log.error(f'Failed to decode ENS name renewed event due to {e!s}')
            return DEFAULT_DECODING_OUTPUT

        name = decoded_data[0]
        name_cost = from_wei(decoded_data[1])
        expires = decoded_data[2]

        refund_event_idx, refund_amount = None, ZERO
        for idx, event in enumerate(context.decoded_events):
            if event.event_type == HistoryEventType.RECEIVE and event.event_subtype == HistoryEventSubType.NONE and event.asset == A_ETH and event.address == context.tx_log.address:  # noqa: E501
                refund_event_idx = idx
                refund_amount = event.balance.amount

            # Find the transfer event which should be before the name renewed event
            if event.event_type == HistoryEventType.SPEND and event.asset == A_ETH and event.balance.amount - refund_amount == name_cost and event.address == context.tx_log.address:  # noqa: E501
                event.balance.amount -= refund_amount  # is now equal to name_cost
                event.event_type = HistoryEventType.RENEW
                event.event_subtype = HistoryEventSubType.NFT
                event.counterparty = CPT_ENS
                event.notes = f'Renew ENS name {name} for {name_cost} ETH until {self.timestamp_to_date(expires)}'  # noqa: E501

        if refund_event_idx is not None:
            del context.decoded_events[refund_event_idx]
        return DEFAULT_DECODING_OUTPUT

    def _decode_ens_registry_with_fallback_event(self, context: DecoderContext) -> DecodingOutput:
        """Decode event where address is set for an ENS name."""
        if context.tx_log.topics[0] == NEW_RESOLVER:
            node = context.tx_log.topics[1]
            try:
                ens_name = self.ethereum.contracts.contract(string_to_evm_address('0xA2C122BE93b0074270ebeE7f6b7292C7deB45047')).call(  # noqa: E501
                    node_inquirer=self.ethereum,
                    method_name='name',
                    arguments=[node],
                )
            except RemoteError as e:
                log.debug(f'Failed to decode ENS set-text event due to {e!s}')
                return DEFAULT_DECODING_OUTPUT

            if ens_name == '':
                # By checking the contract code, I don't think it can happen. But just in case.
                return DEFAULT_DECODING_OUTPUT

            # Not able to give more info to the user such as address that was set since
            # we don't have historical info and event doesn't provide it
            notes = f'Set ENS address for {ens_name}'
            context.decoded_events.append(self.base.make_event_from_transaction(
                transaction=context.transaction,
                tx_log=context.tx_log,
                event_type=HistoryEventType.INFORMATIONAL,
                event_subtype=HistoryEventSubType.NONE,
                asset=A_ETH,
                balance=Balance(),
                location_label=context.transaction.from_address,
                notes=notes,
                counterparty=CPT_ENS,
                address=context.transaction.to_address,
            ))
        return DEFAULT_DECODING_OUTPUT

    def _decode_ens_public_resolver_events(self, context: DecoderContext) -> DecodingOutput:
        """Decode event where a text property (discord, telegram, etc.) is set for an ENS name."""
        if context.tx_log.topics[0] not in (TEXT_CHANGED_KEY_ONLY, TEXT_CHANGED_KEY_AND_VALUE):
            return DEFAULT_DECODING_OUTPUT

        try:
            _, decoded_data = decode_event_data_abi_str(
                context.tx_log,
                TEXT_CHANGED_KEY_ONLY_ABI if context.tx_log.topics[0] == TEXT_CHANGED_KEY_ONLY else TEXT_CHANGED_KEY_AND_VALUE_ABI,  # noqa: E501
            )
        except DeserializationError as e:
            log.error(f'Failed to decode ENS set-text event due to {e!s}')
            return DEFAULT_DECODING_OUTPUT

        changed_key = decoded_data[0]
        new_value = decoded_data[1] if context.tx_log.topics[0] == TEXT_CHANGED_KEY_AND_VALUE else None  # noqa: E501
        node = context.tx_log.topics[1]  # node is a hash of the name used by ens internals
        contract = self.ethereum.contracts.contract_by_address(address=context.tx_log.address)  # Is either public resolver v2 or v3  # noqa: E501

        name_to_show: Optional[str] = None
        if contract is None:
            self.msg_aggregator.add_error(
                f'Failed to find ENS public resolver contract with address '
                f'{context.tx_log.address}. This should never happen. Please, '
                f"open an issue in rotki's github repository.",
            )
        else:
            try:
                address = contract.call(
                    node_inquirer=self.ethereum,
                    method_name='addr',
                    arguments=[node],
                )
            except RemoteError as e:
                log.debug(f'Failed to query ENS name of node {node.hex()} due to: {e!s}')
            else:
                address = to_checksum_address(address)
                ens_mapping = find_ens_mappings(
                    ethereum_inquirer=self.ethereum,
                    addresses=[address],
                    ignore_cache=False,
                )
                name_to_show = ens_mapping.get(address, address)

        notes = f'Set ENS {changed_key} {f"to {new_value} " if new_value else ""}attribute'
        if name_to_show is not None:
            notes += f' for {name_to_show}'
        context.decoded_events.append(self.base.make_event_from_transaction(
            transaction=context.transaction,
            tx_log=context.tx_log,
            event_type=HistoryEventType.INFORMATIONAL,
            event_subtype=HistoryEventSubType.NONE,
            asset=A_ETH,
            balance=Balance(),
            location_label=context.transaction.from_address,
            notes=notes,
            counterparty=CPT_ENS,
            address=context.transaction.to_address,
        ))
        return DEFAULT_DECODING_OUTPUT

    # -- DecoderInterface methods

    def possible_events(self) -> DecoderEventMappingType:
        return {CPT_ENS: {
            HistoryEventType.RENEW: {
                HistoryEventSubType.NFT: EventCategory.RENEW,
            },
            HistoryEventType.TRADE: {
                HistoryEventSubType.SPEND: EventCategory.SWAP_OUT,
                HistoryEventSubType.RECEIVE: EventCategory.SWAP_IN,
            },
            HistoryEventType.INFORMATIONAL: {
                HistoryEventSubType.NONE: EventCategory.INFORMATIONAL,
            },
        }}

    def addresses_to_decoders(self) -> dict[ChecksumEvmAddress, tuple[Any, ...]]:
        return {
            ENS_REGISTRAR_CONTROLLER_1: (self._decode_ens_registrar_event,),
            ENS_REGISTRAR_CONTROLLER_2: (self._decode_ens_registrar_event,),
            ENS_REGISTRY_WITH_FALLBACK: (self._decode_ens_registry_with_fallback_event,),
            ENS_PUBLIC_RESOLVER_2_ADDRESS: (self._decode_ens_public_resolver_events,),
            ENS_PUBLIC_RESOLVER_3_ADDRESS: (self._decode_ens_public_resolver_events,),
        }

    def counterparties(self) -> list[CounterpartyDetails]:
        return [CounterpartyDetails(identifier=CPT_ENS, label='ens', image='ens.svg')]
