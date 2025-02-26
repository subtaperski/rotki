from typing import Any, Union

from marshmallow import Schema, fields, post_load

from rotkehlchen.api.v1.fields import AssetField, AssetTypeField, TimestampField
from rotkehlchen.api.v1.schemas import OptionalEvmTokenInformationSchema, UnderlyingTokenInfoSchema
from rotkehlchen.assets.asset import CryptoAsset, CustomAsset, EvmToken, UnderlyingToken
from rotkehlchen.assets.types import AssetType


class AssetWithOraclesSchema(OptionalEvmTokenInformationSchema):
    def __init__(self, asset_type: AssetType) -> None:
        super().__init__()
        self.asset_type = asset_type

    identifier = fields.String(required=True)
    name = fields.String(required=True)
    symbol = fields.String(required=True)
    forked = AssetField(expected_type=CryptoAsset, required=True, allow_none=True)
    swapped_for = AssetField(expected_type=CryptoAsset, required=True, allow_none=True)
    cryptocompare = fields.String(required=True, allow_none=True)
    coingecko = fields.String(required=True, allow_none=True)
    decimals = fields.Integer(required=False)
    protocol = fields.String(allow_none=True)
    underlying_tokens = fields.List(fields.Nested(UnderlyingTokenInfoSchema), allow_none=True)
    started = TimestampField(required=True, allow_none=True)

    @post_load
    def transform_data(
            self,
            data: dict[str, Any],
            **_kwargs: Any,
    ) -> dict[str, Any]:
        """Returns the a dictionary with:
        - The identifier
        - extra_information used by the globaldb handler
        - name
        - symbol
        - asset_type as instance of AssetType
        """
        given_underlying_tokens = data.pop('underlying_tokens', None)
        underlying_tokens = None
        if given_underlying_tokens is not None:
            underlying_tokens = []
            for entry in given_underlying_tokens:
                underlying_tokens.append(UnderlyingToken(
                    address=entry['address'],
                    weight=entry['weight'],
                    token_kind=data['token_kind'],
                ))

        extra_information: Union[dict[str, Any], EvmToken]
        swapped_for, swapped_for_ident = data.pop('swapped_for'), None
        if swapped_for is not None:
            swapped_for_ident = swapped_for.identifier

        if self.asset_type == AssetType.EVM_TOKEN:
            extra_information = EvmToken.initialize(
                address=data.pop('address'),
                chain_id=data.pop('evm_chain'),
                token_kind=data.pop('token_kind'),
                name=data.get('name'),
                symbol=data.get('symbol'),
                decimals=data.pop('decimals'),
                started=data.pop('started'),
                swapped_for=swapped_for_ident,
                coingecko=data.pop('coingecko'),
                cryptocompare=data.pop('cryptocompare'),
                underlying_tokens=underlying_tokens,
            )
        else:
            forked, forked_ident = data.pop('forked'), None
            if forked is not None:
                forked_ident = forked.identifier

            extra_information = {
                'name': data.get('name'),
                'symbol': data.get('symbol'),
                'started': data.pop('started'),
                'forked': forked_ident,
                'swapper_for': swapped_for_ident,
                'coingecko': data.pop('coingecko'),
                'cryptocompare': data.pop('cryptocompare'),
            }

        data['underlying_tokens'] = underlying_tokens
        data['asset_type'] = self.asset_type
        data['extra_information'] = extra_information
        return data


class CustomAssetSchema(Schema):
    identifier = fields.String(required=True)
    name = fields.String(required=True)
    notes = fields.String(load_default=None)
    custom_asset_type = fields.String(required=True)

    @post_load
    def make_custom_asset(
            self,
            data: dict[str, Any],
            **_kwargs: Any,
    ) -> dict[str, CustomAsset]:
        custom_asset = CustomAsset.initialize(
            identifier=str(data['identifier']),
            name=data['name'],
            notes=data['notes'],
            custom_asset_type=data['custom_asset_type'],
        )
        data['asset_type'] = AssetType.CUSTOM_ASSET
        data['extra_information'] = custom_asset
        return data


class AssetDataSchema(Schema):
    identifier = fields.String(required=True)
    asset_type = AssetTypeField(required=True)

    class Meta:
        unknown = 'include'  # Needed to accept extra arguments depending on asset type

    @post_load
    def transform_data(
            self,
            data: dict[str, Any],
            **_kwargs: Any,
    ) -> dict[str, Any]:
        asset_type = data.pop('asset_type')
        if asset_type == AssetType.CUSTOM_ASSET:
            return CustomAssetSchema().load(data)

        return AssetWithOraclesSchema(asset_type=asset_type).load(data)


class ExportedAssetsSchema(Schema):
    version = fields.String(required=True)
    assets = fields.List(fields.Nested(AssetDataSchema), load_default=None)
