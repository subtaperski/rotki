from typing import Callable, Optional

from rotkehlchen.assets.asset import Asset, AssetWithOracles
from rotkehlchen.assets.exchanges_mappings.binance import WORLD_TO_BINANCE
from rotkehlchen.assets.exchanges_mappings.bitfinex import WORLD_TO_BITFINEX
from rotkehlchen.assets.exchanges_mappings.bitpanda import WORLD_TO_BITPANDA
from rotkehlchen.assets.exchanges_mappings.bitstamp import WORLD_TO_BITSTAMP
from rotkehlchen.assets.exchanges_mappings.bittrex import WORLD_TO_BITTREX
from rotkehlchen.assets.exchanges_mappings.blockfi import WORLD_TO_BLOCKFI
from rotkehlchen.assets.exchanges_mappings.coinbase import WORLD_TO_COINBASE
from rotkehlchen.assets.exchanges_mappings.coinbase_pro import WORLD_TO_COINBASE_PRO
from rotkehlchen.assets.exchanges_mappings.cryptocom import WORLD_TO_CRYPTOCOM
from rotkehlchen.assets.exchanges_mappings.gemeni import WORLD_TO_GEMINI
from rotkehlchen.assets.exchanges_mappings.iconomi import WORLD_TO_ICONOMI
from rotkehlchen.assets.exchanges_mappings.kraken import WORLD_TO_KRAKEN
from rotkehlchen.assets.exchanges_mappings.kucoin import WORLD_TO_KUCOIN
from rotkehlchen.assets.exchanges_mappings.nexo import WORLD_TO_NEXO
from rotkehlchen.assets.exchanges_mappings.okx import WORLD_TO_OKX
from rotkehlchen.assets.exchanges_mappings.poloniex import WORLD_TO_POLONIEX
from rotkehlchen.assets.exchanges_mappings.uphold import WORLD_TO_UPHOLD
from rotkehlchen.assets.utils import symbol_to_asset_or_token
from rotkehlchen.constants.assets import A_DAI, A_SAI
from rotkehlchen.errors.asset import UnsupportedAsset
from rotkehlchen.errors.serialization import DeserializationError
from rotkehlchen.types import Location, Timestamp
from rotkehlchen.utils.misc import ts_now

COINBASE_DAI_UPGRADE_END_TS = 1575244800  # December 2
UNSUPPORTED_POLONIEX_ASSETS = {
    'ACH1',  # neither in coingecko nor cryptocompare
    # This was a super shortlived coin.
    # Only info is here: https://bitcointalk.org/index.php?topic=632818.0
    # No price info in cryptocompare or paprika. So we don't support it.
    'AXIS',
    'APH',
    # This was yet another shortlived coin whose announcement is here:
    # https://bitcointalk.org/index.php?topic=843495 and coinmarketcap:
    # https://coinmarketcap.com/currencies/snowballs/.
    # No price info in cryptocompare or paprika. So we don't support it.
    'BALLS',
    # There are two coins with the name BankCoin, neither of which seems to
    # be this. This market seems to have beend added in May 2014
    # https://twitter.com/poloniex/status/468070096913432576
    # but both other bank coins are in 2017 and 2018 respectively
    # https://coinmarketcap.com/currencies/bankcoin/
    # https://coinmarketcap.com/currencies/bank-coin/
    # So this is an unknown coin
    'BANK',
    # BitBlock seems to be this: https://coinmarketcap.com/currencies/bitblock/
    # and seems to have lived for less than a month. It does not seem to be the
    # same as BBK, the BitBlocks project (https://www.cryptocompare.com/coins/bbk/overview)
    # No price info in cryptocompare or paprika. So we don't support it.
    'BBL',
    # Black Dragon Coin. Seems like a very short lived scam from Russia.
    # Only info that I found is here: https://bitcointalk.org/index.php?topic=597006.0
    # No price info in cryptocompare or paprika. So we don't support it.
    'BDC',
    # Badgercoin. A very shortlived coin. Only info found is here:
    # https://coinmarketcap.com/currencies/badgercoin/
    # Same symbol is used for an active coin called "Bitdegreee"
    # https://coinmarketcap.com/currencies/bitdegree/
    # No price info in cryptocompare or paprika. So we don't support it.
    'BDG',
    # Bonuscoin. A shortlived coin. Only info found is here:
    # https://coinmarketcap.com/currencies/bonuscoin/
    # No price info in cryptocompare or paprika. So we don't support it.
    'BNS',
    # Bonescoin. A shortlived coin. Only info found is here:
    # https://coinmarketcap.com/currencies/bones/
    # No price info in cryptocompare or paprika. So we don't support it.
    'BONES',
    # Burnercoin. A shortlived coind Only info is here:
    # https://coinmarketcap.com/currencies/burnercoin/
    # No price info in cryptocompare or paprika. So we don't support it.
    'BURN',
    # Colbertcoin. Shortlived coin. Only info is here:
    # https://coinmarketcap.com/currencies/colbertcoin/
    # No price info in cryptocompare or paprika. So we don't support it.
    'CC',
    # Chancecoin.
    # https://coinmarketcap.com/currencies/chancecoin/
    'CHA',
    # C-note. No data found anywhere. Only this:
    # https://bitcointalk.org/index.php?topic=397916.0
    'CNOTE',
    # Coino. Shortlived coin with only data found here
    # https://coinmarketcap.com/currencies/coino/
    # A similar named token, coin(o) with symbol CNO has data
    # both in cmc and paprika, but CON doesn't so we don't support it
    'CON',
    # CORE (CORE) but cc and coingecko have cvault
    'CORE',
    # CorgiCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/corgicoin/
    'CORG',
    # Neodice. No data found except from here:
    # https://coinmarketcap.com/currencies/neodice/
    # A lot more tokens with the DICE symbol exist so we don't support this
    'DICE',
    # Distrocoin. No data found except from here:
    # https://coinmarketcap.com/currencies/distrocoin/
    'DIS',
    # Bitshares DNS. No data found except from here:
    # https://coin.market/crypto/dns
    'DNS',
    # DvoraKoin. No data found except from here:
    # https://bitcointalk.org/index.php?topic=613854.0
    'DVK',
    # EBTcoin. No data found except from here:
    # https://coinmarketcap.com/currencies/ebtcoin/
    'EBT',
    # EmotiCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/emoticoin/
    'EMO',
    # EntropyCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/entropycoin/
    'ENC',
    # eToken. No data found except from here:
    # https://coinmarketcap.com/currencies/etoken/
    'eTOK',
    # ETHBNT. No data found outside of poloniex:
    # https://poloniex.com/exchange#btc_ethbnt
    'ETHBNT',
    # FoxCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/foxcoin/
    'FOX',
    # FairQuark. No data found except from here:
    # https://coinmarketcap.com/currencies/fairquark/
    'FREE',
    'FRQ',
    # FVZCoin. No data found except from here:
    # https://coin.market/crypto/fvz
    'FVZ',
    # Frozen. No data found except from here:
    # https://coinmarketcap.com/currencies/frozen/
    'FZ',
    # Fuzon. No data found except from here:
    # https://coinmarketcap.com/currencies/fuzon/
    'FZN',
    # Global Denomination. No data found except from here:
    # https://coinmarketcap.com/currencies/global-denomination/
    'GDN',
    # Giarcoin. No data found except from here:
    # https://bitcointalk.org/index.php?topic=545529.0
    'GIAR',
    # Globe. No data found except from here:
    # https://coinmarketcap.com/currencies/globe/
    'GLB',
    # GenesisCoin. No data found except from here:
    # https://bitcointalk.org/index.php?topic=518258.0
    'GNS',
    # GoldEagles. No data found.
    'GOLD',
    # GroupCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/groupcoin/
    'GPC',
    # Gridcoin X. Not sure what this is. Perhaps a fork of Gridcoin
    # https://coinmarketcap.com/currencies/gridcoin-classic/#charts
    # In any case only poloniex lists it for a bit so ignoring it
    'GRCX',
    # H2Ocoin. No data found except from here:
    # https://coinmarketcap.com/currencies/h2ocoin/
    'H2O',
    # Hirocoin. No data found except from here:
    # https://coinmarketcap.com/currencies/hirocoin/
    'HIRO',
    # Hotcoin. Super shortlived. No data found except from here:
    # https://coinmarketcap.com/currencies/hotcoin/
    # Note there are 2 more coins with this symbol.
    # https://coinmarketcap.com/currencies/hydro-protocol/
    # https://coinmarketcap.com/currencies/holo/
    'HOT',
    # CoinoIndex. No data found except from here:
    # https://coinmarketcap.com/currencies/coinoindex/
    'INDEX',
    # InformationCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/informationcoin/
    'ITC',
    # jl777hodl. No data found except from here:
    # https://coinmarketcap.com/currencies/jl777hodl/
    'JLH',
    # Jackpotcoin. No data found except from here:
    # https://coinmarketcap.com/currencies/jackpotcoin/
    'JPC',
    # Juggalocoin. No data found except from here:
    # https://bitcointalk.org/index.php?topic=555896.0
    'JUG',
    # KTON - Darwinia commitment token. No data found
    'KTON',
    # Limecoin. No data found except from here:
    # https://coinmarketcap.com/currencies/limecoin/
    'LC',
    # LimecoinLite. No data found except from here:
    # https://coinmarketcap.com/currencies/limecoinlite/
    'LCL',
    # LogiCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/logicoin/
    'LGC',
    # LeagueCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/leaguecoin/
    'LOL',
    # LoveCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/lovecoin/
    'LOVE',
    # Mastiffcoin. No data found except from here:
    # https://coinmarketcap.com/currencies/mastiffcoin/
    'MAST',
    # CryptoMETH. No data found except from here:
    # https://coinmarketcap.com/currencies/cryptometh/
    'METH',
    # Millenium coin. No data found except from here:
    # https://coinmarketcap.com/currencies/millenniumcoin/
    'MIL',
    # Moneta. No data found except from here:
    # https://coinmarketcap.com/currencies/moneta/
    # There are other moneta coins like this:
    # https://www.cryptocompare.com/coins/moneta/overview/BTC
    # but they don't seem to bethe same
    'MNTA',
    # Monocle. No data found except from here:
    # https://coinmarketcap.com/currencies/monocle/
    'MON',
    # MicroCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/microcoin/
    'MRC',
    # Metiscoin. No data found except from here:
    # https://coinmarketcap.com/currencies/metiscoin/
    'MTS',
    # Muniti. No data found except from here:
    # https://coinmarketcap.com/currencies/muniti/
    'MUN',
    # N5coin. No data found except from here:
    # https://coinmarketcap.com/currencies/n5coin/
    'N5X',
    # NAS. No data found except from here:
    # https://coinmarketcap.com/currencies/nas/
    # Note: This is not the Nebulas NAS token
    'NAS',
    # Nanolite. No data found except from here:
    # https://www.reddit.com/r/CryptoCurrency/comments/26neqz/nanolite_a_new_x11_cryptocurrency_which_launched/
    'NL',
    # NobleNXT. No data found except from here:
    # https://coinmarketcap.com/currencies/noblenxt/
    'NOXT',
    # NTX. No data found except from here:
    # https://coinmarketcap.com/currencies/ntx/
    'NTX',
    # (PAND)a coin. No data found except here:
    # https://coinmarketcap.com/currencies/pandacoin-panda/
    # Note: This is not the PND Panda coin
    'OSK',  # Missing coingecko/cc information
    'PAND',
    # Pawncoin. No data found except from here:
    # https://coinmarketcap.com/currencies/pawncoin/
    'PAWN',
    # Parallaxcoin. No data found except from here:
    # https://coinmarketcap.com/currencies/parallaxcoin/
    # Note: This is not PLEX coin
    'PLX',
    # Premine. No data found except from here:
    # https://coinmarketcap.com/currencies/premine/
    'PMC',
    # Particle. No data found except from here:
    # https://coinmarketcap.com/currencies/particle/
    'PRT',
    # Bitshares PTS. No data found except from here:
    # https://coinmarketcap.com/currencies/bitshares-pts/
    'PTS',
    # ShibeCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/shibecoin/
    'SHIBE',
    # ShopX. No data found except from here:
    # https://coinmarketcap.com/currencies/shopx/
    'SHOPX',
    # SocialCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/socialcoin/
    # Note this is not The SOCC Social coin
    # https://coinmarketcap.com/currencies/socialcoin-socc/
    'SOC',
    # SourceCoin. No data found except from here:
    # https://bitcointalk.org/index.php?topic=688494.160
    'SRCC',
    # SurgeCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/surgecoin/
    'SRG',
    # SummerCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/summercoin/
    'SUM',
    # SunCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/suncoin/
    'SUN',
    # TalkCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/talkcoin/
    'TAC',
    # Twecoin. No data found except from here:
    # https://bitcointalk.org/index.php?topic=553593.0
    'TWE',
    # UniversityCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/universitycoin/
    'UVC',
    # Voxels. No data found except from here:
    # https://coincodex.com/crypto/voxels/
    'VOX',
    'VRA',
    # X13 coin. No data found. Except from maybe this:
    # https://bitcointalk.org/index.php?topic=635382.200;wap2
    'X13',
    # ApiCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/apicoin/
    'XAP',
    # Xcurrency. No data found except from here:
    # https://coinmarketcap.com/currencies/xcurrency/
    'XC',
    # ClearingHouse. No data found except from here:
    # https://coinmarketcap.com/currencies/clearinghouse/
    'XCH',
    # Filecoin IOU. No data found for this except from in poloniex.
    # As of 22/07/2020
    'XFIL',
    # HonorCoin. No data found except from here:
    # https://bitcointalk.org/index.php?topic=639043.0
    'XHC',
    # SilliconValleyCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/siliconvalleycoin-old/
    'XSV',
    # CoinoUSD. No data found except from here:
    # https://coinmarketcap.com/currencies/coinousd/
    'XUSD',
    # Creds. No data found except from here:
    # https://bitcointalk.org/index.php?topic=513483.0
    'XXC',
    # YangCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/yangcoin/
    'YANG',
    # YellowCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/yellowcoin/
    'YC',
    # YinCoin. No data found except from here:
    # https://coinmarketcap.com/currencies/yincoin/
    'YIN',
    # Bitcoin and Volatility and Inverse volatility token.
    # No data found yet but should probably revisit. They are
    # in cryptocompare but they have no price
    'BVOL',
    'IBVOL',
    'XDOT',  # old polkadot before the split
    'BCC',  # neither in coingecko nor cryptocompare
    'BTCTRON',  # neither in coingecko nor cryptocompare
    'FCT2',  # neither in coingecko nor cryptocompare
    'XFLR',  # neither in coingecko nor cryptocompare (is an iou for FLR - SPARK)
    'SUNX',  # neither in coingecko nor cryptocompare
    'SQUID',  # neither in coingecko nor cryptocompare
    'XCNOLD',  # No info in the exchange about this asset
    'USDTEARN1',  # neither in coingecko nor cryptocompare
    'LOGT',  # lord of dragon but not in cc or coingecko
    'OPT',
    'SOV',
    'WSTREETBABY',
    'GEKE',
    'BAM',
    'LZM',
}

UNSUPPORTED_BITTREX_ASSETS = {
    # 4ART, As of 22/07/2020 no data found outside of Bittrex
    '4ART',
    # APIX, As of 19/12/2019 no data found outside of Bittrex
    # https://medium.com/apisplatform/apix-trading-open-on-bittrex-global-61653fa346fa
    'APIX',
    # APM Coin. As of 16/11/2019 no data found outside of Bittrex for this token
    # https://global.bittrex.com/Market/Index?MarketName=BTC-APM
    'APM',
    'ARTII',  # neither in coingecko nor cryptocompare
    'BTR',  # neither in coingecko nor cryptocompare
    'BST',  # No coingecko or cryptocompare yet. Beshare Token TODO: Review this one in a few days
    'CADX',  # no cryptocompare/coingecko data TODO: Review this one
    'CAST',  # castello but no cc/cryptocompare
    'CBC',  # neither in coingecko nor cryptocompare
    'CIND',  # neither in coingecko nor cryptocompare
    'CLI',  # Couldn't find a reference to this asset
    # Tether CNH. As of 30/09/2019 no data found outside of Bittrex for this token
    # https://medium.com/bittrex/new-bittrex-international-listing-tether-cnh-cnht-c9ad966ac303
    'CNHT',
    'CWD',
    'DECE',
    'DAF',  # neither in coingecko nor cryptocompare
    'DATA',  # Couldn't find what token this is
    'MPC',  # neither in coingecko nor cryptocompare
    # Foresting. As of 22/03/2019 no data found.
    # Only exists in bittrex. Perhaps it will soon be added to other APIs.
    # https://international.bittrex.com/Market/Index?MarketName=BTC-PTON
    'PTON',
    # VDX IEO. As of 16/05/2019 no data found.
    # Only exists in bittrex. Perhaps it will soon be added to other APIs.
    # https://international.bittrex.com/Market/Index?MarketName=BTC-VDX
    'VDX',
    # Origo. As of 02/06/2019 no data found outside of bittrex
    # https://international.bittrex.com/Market/Index?MarketName=BTC-OGO
    'OGO',
    # OriginChain. As of 29/01/2021 no cryptocompare/coingecko data
    # https://medium.com/bittrexglobal/new-listing-originchain-ogt-b119736dd3f6
    'OGT',
    # STPT. As of 06/06/2019 no data found outside of bittrex
    # https://twitter.com/BittrexIntl/status/1136045052164227079
    'STPT',
    # PHNX. As of 07/06/2020 no data found outside of bittrex for PhoenixDAO
    # https://www.coingecko.com/en/coins/phoenixdao
    'PHNX',
    # PROM. As of 28/06/2019 no data found outside of bittrex for Prometheus
    # https://twitter.com/BittrexIntl/status/1144290718325858305
    'PROM',
    # URAC. As of 12/07/2019 no data found outside of bittrex for Uranus
    # https://twitter.com/BittrexIntl/status/1149370485735591936
    'URAC',
    # BRZ. As of 16/06/2019 no data found outside of Bittrex for this token
    # https://twitter.com/BittrexIntl/status/1150870819758907393
    'BRZ',
    'DRCM',  # neither in coingecko nor cryptocompare
    'ETM',  # neither in coingecko nor cryptocompare
    # HINT. As of 28/07/2019 no data found outside of Bittrex for this token
    # https://twitter.com/BittrexIntl/status/1154445165257474051
    'HINT',
    'HRTS',  # no cc/cryptocompare data
    # TUDA. As of 02/08/2019 no data found outside of Bittrex for this token
    # https://mobile.twitter.com/BittrexIntl/status/1156974900986490880
    'TUDA',
    # TwelveShips. As of 23/08/2019 no data found outside of Bittrex for this token
    # https://twitter.com/BittrexIntl/status/1164689364997353472
    'TSHP',
    # BlockTV. As of 29/11/2019 no data found outside of Bittrex for this token
    # https://global.bittrex.com/Market/Index?MarketName=BTC-BLTV
    'BLTV',
    'BTD',  # bitdesk but no cc/coingecko
    # Forkspot. As for 01/03/2020 no data found outside of Bittrex for this token
    # https://global.bittrex.com/Market/Index?MarketName=BTC-FRSP
    'FRSP',
    'PIST',  # neither in coingecko nor cryptocompare
    # Universal Protocol Token. As of 19/03/2020 no data found outside of Bittrex for this token.
    # https://global.bittrex.com/Market/Index?MarketName=BTC-UPT
    'UPT',
    # Universal USD and EUR. As of 19/03/2020 no data found outside of Bittrex for this token.
    # https://global.bittrex.com/Market/Index?MarketName=BTC-UPUSD
    'UPEUR',
    'UPUSD',
    # Vanywhere. As of 19/03/2020 no data found outside of Bittrex for this token.
    # https://global.bittrex.com/Market/Index?MarketName=BTC-VANY
    'VANY',
    # Ecochain. As of 22/07/2020 no data found outside of Bittrex for this token.
    # All ECOC data refer to a different coin called EcoCoin
    'ECOC',
    'EDG',
    'EXO',  # neither in coingecko nor cryptocompare
    'EXVA',  # neither in coingecko nor cryptocompare
    # As of 28/08/2020 the following assets don't have prices listed anywhere
    'FME',
    'FOL',  # neither in coingecko nor cryptocompare
    'GET',  # couldn't find any reference
    'INX',
    'JASMY',  # neither in coingecko nor cryptocompare
    'KBH',  # K black hole but not in coingecko/cc
    'MFA',
    'FCT2',  # neither in coingecko nor cryptocompare
    'PAR',  # Couldn't find what asset is this
    'UPXAU',  # neither in coingecko nor cryptocompare
    'TEA',  # neither in coingecko nor cryptocompare
    'TYB',  # neither in coingecko nor cryptocompare
    'PANDO',  # neither in coingecko nor cryptocompare (own blockchain, released on 2020)
    'SMBSWAP',  # neither in coingecko nor cryptocompare
    'SML',  # neither in coingecko nor cryptocompare
    'SQUID',  # neither in coingecko nor cryptocompare
    'UPCO2',  # neither in coingecko nor cryptocompare
    'VIL',  # neither in coingecko nor cryptocompare (VICDeal)
    'WIHC',  # neither in coingecko nor cryptocompare
    'WXBTC',  # neither in coingecko nor cryptocompare
    'XBN',  # neither in coingecko nor cryptocompare
    'XSILV',  # No information found about its relation with XGOLD
    'ZILD',  # neither in coingecko nor cryptocompare
    'ZK',  # couldn't find what asset is this
    'GBIT',  # neither in coingecko nor cryptocompare
    'MCCX',  # neither in coingecko nor cryptocompare
    # bittrex tokenized stocks -- not sure how to handle yet
    'AAPL',
    'ABNB',
    'ACB',
    'AMD',
    'AMC',
    'AMZN',
    'APHA',
    'ARKK',
    'BABA',
    'BB',
    'BILI',
    'BITW',
    'BNTX',
    'BYND',
    'FB',
    'GDXJ',
    'GME',
    'GLD',
    'GLXY',
    'GOOGL',
    'MRNA',
    'MSTR',
    'NFLX',
    'NOK',
    'NVDA',
    'PENN',
    'PFE',
    'PYPL',
    'SLV',  # iShares Silver Trust
    'SPY',
    'SQ',
    'TSLA',
    'TSM',
    'TWTR',
    'UBER',
    'USO',
    'ZM',
    '1ECO',
    'CWC',
    'GIGX',
    'GPX',
    'IQO',
    'CAIZ',
    'SIRS',
    'VOLTINU',
    'TZBTC',
    'DST',  # Daystarter but no cc/cryptocompare data
    'AIN',
    'CLXY',
    'MPLC',
    'PRMX',
    'TCR',
    'USDS',
}


UNSUPPORTED_BINANCE_ASSETS = {
    'ETF',  # ETF is a dead coin given to all ETH holders. Just ignore
    # BTCB, USDSB, BGBP are not yet supported anywhere else
    'BTCB',  # https://www.binance.com/en/support/articles/360029288972
    'USDSB',  # https://www.binance.com/en/support/articles/360029522132
    'BGBP',  # https://www.binance.com/en/support/articles/360030827252
    'TUSDB',  # https://www.binance.com/en/support/articles/360032154071
    'NGN',  # https://www.binance.com/en/support/articles/360035511611
    '123',  # https://twitter.com/rotkiapp/status/1161977327078838272
    '456',  # https://twitter.com/rotkiapp/status/1161977327078838272
    '1INCHDOWN',  # no cryptocompare/coingecko data
    '1INCHUP',  # no cryptocompare/coingecko data
    'SXPDOWN',  # no cryptocompare/coingecko data
    'SXPUP',  # no cryptocompare/coingecko data
    'AAVEDOWN',  # no cryptocompare/coingecko data
    'AAVEUP',  # no cryptocompare/coingecko data
    'SUSHIDOWN',  # no cryptocompare/coingecko data
    'SUSHIUP',  # no cryptocompare/coingecko data
    'XLMDOWN',  # no cryptocompare/coingecko data
    'XLMUP',  # no cryptocompare/coingecko data
    'UAH',  # no cryptocompare/coingecko data
    'BTTC',  # no cryptocompare/coingecko data
    'USD4',  # no info available about this asset
    'FLOKI8',  # no info available about this asset
    'ARS',  # no info available about this asset
}

UNSUPPORTED_BITFINEX_ASSETS = {
    'B21X',  # no cryptocompare/coingecko data
    'GTX',  # no cryptocompare/coingecko data (GT, Gate.io token)
    'IQX',  # no cryptocompare/coingecko data (EOS token)
    'IDX',  # no cryptocompare/coingecko data
    'CHEX',  # no cryptocompare/coingecko data (chintai)
    'PLANETS',  # PlanetWatch (PLANETS) but has no cryptocompare/coingecko
    'MCS',  # no cryptocompare/coingecko data yet
    'EXO',  # noqa: E501 #  https://blog.exordium.co/exo-security-token-to-be-listed-on-bitfinex-securities-ltd-24cb03dc8bb0 no cc/coingecko data
    'BMN',  # no cryptocompare and coingecko doesn't update it
    'LUXO',  # no cc/coingecko data
}

# https://api.kucoin.com/api/v1/currencies
UNSUPPORTED_KUCOIN_ASSETS = {
    'AAVE3L',  # no cryptocompare/coingecko data
    'AAVE3S',  # no cryptocompare/coingecko data
    'AI',  # no cryptocompare/coingecko data
    'AVAX3L',  # no cryptocompare/coingecko data
    'AVAX3S',  # no cryptocompare/coingecko data
    'AXE',  # delisted
    'BCH3L',  # no cryptocompare/coingecko data
    'BCH3S',  # no cryptocompare/coingecko data
    'BNB3L',  # no cryptocompare/coingecko data
    'BNB3S',  # no cryptocompare/coingecko data
    'BTC3L',  # no cryptocompare/coingecko data
    'BTC3S',  # no cryptocompare/coingecko data
    'BTCP',  # delisted
    'CADH',  # no cryptocompare/coingecko data
    'CBC',  # neither in coingecko nor cryptocompare
    'CWAR',  # neither in coingecko nor cryptocompare
    'DOGE3L',  # no cryptocompare/coingecko data
    'DOGE3S',  # no cryptocompare/coingecko data
    'DOT3L',  # no cryptocompare/coingecko data
    'DOT3S',  # no cryptocompare/coingecko data
    'EOS3L',  # no cryptocompare/coingecko data
    'EOS3S',  # no cryptocompare/coingecko data
    'EPRX',  # delisted and no cryptocompare/coingecko data
    'ETH3L',  # no cryptocompare/coingecko data
    'ETH3S',  # no cryptocompare/coingecko data
    'ETF',  # delisted and no cryptocompare/coingecko data
    'FTG',  # no cryptocompare/coingecko data
    'GENS',  # Genesis. no cryptocompare/coingecko data
    'GGC',  # delisted and no cryptocompare/coingecko data
    'GMB',  # delisted
    'GOD',  # delisted
    'GZIL',  # delisted
    'HOTCROSS',  # no cryptocompare/coingecko data
    'KTS',  # delisted
    'LINK3L',  # no cryptocompare/coingecko data
    'LINK3S',  # no cryptocompare/coingecko data
    'LITH',  # no cryptocompare/coingecko data
    'LUNA3L',  # no cryptocompare/coingecko data
    'LUNA3S',  # no cryptocompare/coingecko data
    'LOL',  # delisted
    'LSS',  # no cryptocompare/coingecko data
    'LTC3L',  # no cryptocompare/coingecko data
    'LTC3S',  # no cryptocompare/coingecko data
    'MANA3L',  # no cryptocompare/coingecko data
    'MANA3S',  # no cryptocompare/coingecko data
    'MATIC3L',  # no cryptocompare/coingecko data
    'MATIC3S',  # no cryptocompare/coingecko data
    'MAP2',  # delisted
    'MEM',  # meme.com, no cryptocompare/coingecko data
    'NAKA',  # Nakamoto.games, no cryptocompare/coingecko data
    'NEAR3L',  # no cryptocompare/coingecko data
    'NEAR3S',  # no cryptocompare/coingecko data
    'SAND3L',  # no cryptocompare/coingecko data
    'SAND3S',  # no cryptocompare/coingecko data
    'SATT',  # delisted
    'SERO',  # delisted
    'SHILL',  # The one in kucoin is not at coingecko/cc
    'SOL3L',  # no cryptocompare/coingecko data
    'SOL3S',  # no cryptocompare/coingecko data
    'SOV',  # Couldn't find what assets is this one
    'SPRK',  # delisted
    'SWP',  # Couldn't find a list anouncement about this asset
    'SUSHI3L',  # no cryptocompare/coingecko data
    'SUSHI3S',  # no cryptocompare/coingecko data
    'TCP',  # The Crypto Prophecies no cryptocompare/coingecko data
    'TNC2',  # delisted and no cryptocompare/coingecko data
    'TT',  # delisted
    'VET3L',  # no cryptocompare/coingecko data
    'VET3S',  # no cryptocompare/coingecko data
    'VNX',  # delisted and no cryptocompare/coingecko data
    'VOL',  # delisted
    'ADA3S',  # no cryptocompare/coingecko data
    'ADA3L',  # no cryptocompare/coingecko data
    'FEAR',  # no cryptocompare/coingecko data
    'DAPPX',  # no cryptocompare/coingecko data
    'OOE',  # no cryptocompare/coingecko data
    'ROAR',  # no cryptocompare/coingecko data *alphadex coin
    'SPHRI',  # no cryptocompare/coingecko data SpheriumFinance
    'MUSH',  # Couldn't find a listing post saying what asset is this one
    'MAKI',  # Couldn't find information about this asset at kucoin. Seems like is not public yet
    'PBX',  # no cryptocompare/coingecko data
    'XNL',  # no cryptocompare/coingecko data
    'XRP3L',  # no cryptocompare/coingecko data
    'XRP3S',  # no cryptocompare/coingecko data
    'UNI3L',  # no cryptocompare/coingecko data
    'UNI3S',  # no cryptocompare/coingecko data
    'ATOM3L',  # no cryptocompare/coingecko data
    'ATOM3S',  # no cryptocompare/coingecko data
    'FTM3L',  # no cryptocompare/coingecko data
    'FTM3S',  # no cryptocompare/coingecko data
    'AXS3L',  # no cryptocompare/coingecko data
    'AXS3S',  # no cryptocompare/coingecko data
    'GALAX3L',  # no cryptocompare/coingecko data
    'GALAX3S',  # no cryptocompare/coingecko data
    'KDON',  # no cryptocompare/coingecko data
    'ELITEHERO',  # no cryptocompare/coingecko data
    'FCD',  # freshcut diamon not in cc/coingecko yet
    'XRACER',  # no cryptocompare/coingecko data
    'APE3L',  # no cryptocompare/coingecko data
    'APE3S',  # no cryptocompare/coingecko data
    'GMT3L',  # no cryptocompare/coingecko data
    'GMT3S',  # no cryptocompare/coingecko data
    'JASMY3L',  # no cryptocompare/coingecko data
    'JASMY3S',  # no cryptocompare/coingecko data
    'SRBP',  # no cryptocompare/coingecko data
    'RBP',  # no cryptocompare/coingecko data
    'IDLENFT',  # no cryptocompare/coingecko data
    'RBS',  # no cryptocompare/coingecko data
    'HIMAYC',  # no cryptocompare/coingecko data
    'PRMX',  # no cryptocompare/coingecko data
    'ASTROBOY',  # no cc/coingecko data
    'HIOD',  # no cc/coingecko data
    'HIVALHALLA',  # no cc/coingecko data
    'HIBIRDS',  # no cc/coingecko data
    'ASTRA',  # no cc/coingecko data
    'CLUB',  # no cc/coingecko data
    'TEM',  # no cc/coingecko data
    'SHIB2L',
    'SHIB2S',
    'APT2L',
    'APT2S',
    'OP2L',
    'OP2S',
    'BLUR2L',
    'BLUR2S',
    'CFX2L',
    'CFX2S',
    'AGIX2L',
    'AGIX2S',
    'GRT2L',
    'GRT2S',
    'AGIX2L',
    'AGIX2S',
    'HISEALS',  # no cc/coingecko data
    'HIRENGA',
    'HIGH',
    'KING',
    'HIUNDEAD',
    'HIFRIENDS',
    'PEPEUP',
    'PEPEDOWN',
    'ICPUP',
    'ICPDOWN',
    'CTSIUP',
    'CTSIDOWN',
    'SUI3L',
    'SUI3S',
    'ETCDOWN',
    'ETCUP',
    'INJUP',
    'INJDOWN',
    'LINAUP',
    'LINADOWN',
    'RNDRUP',
    'RNDRDOWN',
    'STXDOWN',
    'STXUP',
    'DYDXUP',
    'DYDXDOWN',
    'MASKUP',
    'MASKDOWN',
    'ARB3S',
    'ARB3L',
    'ID3L',
    'ID3S',
    'OPT',  # optimus token but no coingecko/cc
    'AOS',  # no coingecko/cc
    'KAGI',
    'SXPUP',
    'SXPDOWN',
    'FLOKIUP',
    'FLOKIDOWN',
    'KAVAUP',
    'KAVADOWN',
    'ZILUP',
    'LUNCDOWN',
    'LUNCUP',
    'WOOUP',
    'WOODOWN',
    'SUIA',
    'ZILDOWN',
}

# https://api.iconomi.com/v1/assets marks delisted assets
UNSUPPORTED_ICONOMI_ASSETS = {
    'ICNGS',
    'ETCPOLO',
    'FTR',  # delisted
    'TT',  # delisted
}

UNSUPPORTED_GEMINI_ASSETS = {
    '2USD',  # no information about this asset
    'AUSD',  # no information about this asset
    'LFIL',  # no information about this asset
    'LGBP',  # no information about this asset
    'LSGD',  # no information about this asset
    'LEUR',  # no information about this asset
    'LHKD',  # no information about this asset
    'LCAD',  # no information about this asset
    'LAUD',  # no information about this asset
    'SPEL',  # Spell moon (SPEL). No information about this token
}

UNSUPPORTED_OKX_ASSETS = {
    'CORE',  # CORE(CORE) but APIs list cvault
    'GALFT',  # not in cc or coingecko
    'SOLO',  # no information about this listing
    'EC',  # not in cc or coingecko
    'GOAL',  # not in cc or coingecko
    'CGL',  # not in cc or coingecko
    'OPTIMUS',
}

# Exchange symbols that are clearly for testing purposes. They appear in all
# these places: supported currencies list, supported exchange pairs list and
# currency map.
BITFINEX_EXCHANGE_TEST_ASSETS = (
    'AAA',
    'BBB',
    'TESTBTC',
    'TESTBTCF0',
    'TESTUSD',
    'TESTUSDT',
    'TESTUSDTF0',
)

POLONIEX_TO_WORLD = {v: k for k, v in WORLD_TO_POLONIEX.items()}
BITTREX_TO_WORLD = {v: k for k, v in WORLD_TO_BITTREX.items()}
BINANCE_TO_WORLD = {v: k for k, v in WORLD_TO_BINANCE.items()}
BITFINEX_TO_WORLD = {v: k for k, v in WORLD_TO_BITFINEX.items()}
KRAKEN_TO_WORLD = {v: k for k, v in WORLD_TO_KRAKEN.items()}
KUCOIN_TO_WORLD = {v: k for k, v, in WORLD_TO_KUCOIN.items()}
ICONOMI_TO_WORLD = {v: k for k, v in WORLD_TO_ICONOMI.items()}
COINBASE_PRO_TO_WORLD = {v: k for k, v in WORLD_TO_COINBASE_PRO.items()}
COINBASE_TO_WORLD = {v: k for k, v in WORLD_TO_COINBASE.items()}
UPHOLD_TO_WORLD = {v: k for k, v in WORLD_TO_UPHOLD.items()}
BITSTAMP_TO_WORLD = {v: k for k, v in WORLD_TO_BITSTAMP.items()}
GEMINI_TO_WORLD = {v: k for k, v in WORLD_TO_GEMINI.items()}
NEXO_TO_WORLD = {v: k for k, v in WORLD_TO_NEXO.items()}
BITPANDA_TO_WORLD = {v: k for k, v in WORLD_TO_BITPANDA.items()}
CRYPTOCOM_TO_WORLD = {v: k for k, v in WORLD_TO_CRYPTOCOM.items()}
BLOCKFI_TO_WORLD = {v: k for k, v in WORLD_TO_BLOCKFI.items()}
OKX_TO_WORLD = {v: k for k, v in WORLD_TO_OKX.items()}

RENAMED_BINANCE_ASSETS = {
    # The old BCC in binance forked into BCHABC and BCHSV
    # but for old trades the canonical chain is ABC (BCH in rotkehlchen)
    'BCC': 'BCH',
    # HCash (HSR) got swapped for Hyperchash (HC)
    # https://support.binance.com/hc/en-us/articles/360012489731-Binance-Supports-Hcash-HSR-Mainnet-Swap-to-HyperCash-HC-
    'HSR': 'HC',
    # Red pulse got swapped for Phoenix
    # https://support.binance.com/hc/en-us/articles/360012507711-Binance-Supports-Red-Pulse-RPX-Token-Swap-to-PHOENIX-PHX-
    'RPX': 'PHX',
}


def asset_from_kraken(kraken_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnknownAsset
    """
    if not isinstance(kraken_name, str):
        raise DeserializationError(f'Got non-string type {type(kraken_name)} for kraken asset')

    if kraken_name.endswith(('.S', '.M')):
        # this is a staked coin. For now since we don't show staked coins
        # consider it as the normal version. In the future we may perhaps
        # differentiate between them in the balances https://github.com/rotki/rotki/issues/569
        kraken_name = kraken_name[:-2]

    if kraken_name.endswith('.HOLD'):
        kraken_name = kraken_name[:-5]

    # Some names are not in the map since kraken can have multiple representations
    # depending on the pair for the same asset. For example XXBT and XBT, XETH and ETH,
    # ZUSD and USD
    if kraken_name == 'SETH':
        name = 'ETH2'
    elif kraken_name == 'XBT':
        name = 'BTC'
    elif kraken_name == 'XDG':
        name = 'DOGE'
    elif kraken_name in ('ETH', 'EUR', 'USD', 'GBP', 'CAD', 'JPY', 'KRW', 'CHF', 'AUD'):
        name = kraken_name
    else:
        name = KRAKEN_TO_WORLD.get(kraken_name, kraken_name)
    return symbol_to_asset_or_token(name)


def asset_from_poloniex(poloniex_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(poloniex_name, str):
        raise DeserializationError(f'Got non-string type {type(poloniex_name)} for poloniex asset')

    if poloniex_name in UNSUPPORTED_POLONIEX_ASSETS:
        raise UnsupportedAsset(poloniex_name)

    our_name = POLONIEX_TO_WORLD.get(poloniex_name, poloniex_name)
    return symbol_to_asset_or_token(our_name)


def asset_from_bitfinex(
        bitfinex_name: str,
        currency_map: dict[str, str],
        is_currency_map_updated: bool = True,
) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset

    Currency map coming from `<Bitfinex>._query_currency_map()` is already
    updated with BITFINEX_TO_WORLD (prevent updating it on each call)
    """
    if not isinstance(bitfinex_name, str):
        raise DeserializationError(f'Got non-string type {type(bitfinex_name)} for bitfinex asset')

    if bitfinex_name in UNSUPPORTED_BITFINEX_ASSETS:
        raise UnsupportedAsset(bitfinex_name)

    if is_currency_map_updated is False:
        currency_map.update(BITFINEX_TO_WORLD)

    symbol = currency_map.get(bitfinex_name, bitfinex_name)
    return symbol_to_asset_or_token(symbol)


def asset_from_bitstamp(bitstamp_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(bitstamp_name, str):
        raise DeserializationError(f'Got non-string type {type(bitstamp_name)} for bitstamp asset')

    # bitstamp assets are read as lowercase from the exchange
    name = BITSTAMP_TO_WORLD.get(bitstamp_name.upper(), bitstamp_name)
    return symbol_to_asset_or_token(name)


def asset_from_bittrex(bittrex_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(bittrex_name, str):
        raise DeserializationError(f'Got non-string type {type(bittrex_name)} for bittrex asset')

    if bittrex_name in UNSUPPORTED_BITTREX_ASSETS:
        raise UnsupportedAsset(bittrex_name)

    name = BITTREX_TO_WORLD.get(bittrex_name, bittrex_name)
    return symbol_to_asset_or_token(name)


def asset_from_coinbasepro(coinbase_pro_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(coinbase_pro_name, str):
        raise DeserializationError(
            f'Got non-string type {type(coinbase_pro_name)} for '
            f'coinbasepro asset',
        )
    name = COINBASE_PRO_TO_WORLD.get(coinbase_pro_name, coinbase_pro_name)
    return symbol_to_asset_or_token(name)


def asset_from_binance(binance_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(binance_name, str):
        raise DeserializationError(f'Got non-string type {type(binance_name)} for binance asset')

    if binance_name in UNSUPPORTED_BINANCE_ASSETS:
        raise UnsupportedAsset(binance_name)

    if binance_name in RENAMED_BINANCE_ASSETS:
        return Asset(RENAMED_BINANCE_ASSETS[binance_name]).resolve_to_asset_with_oracles()

    name = BINANCE_TO_WORLD.get(binance_name, binance_name)
    return symbol_to_asset_or_token(name)


def asset_from_coinbase(cb_name: str, time: Optional[Timestamp] = None) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnknownAsset
    """
    # During the transition from DAI(SAI) to MCDAI(DAI) coinbase introduced an MCDAI
    # wallet for the new DAI during the transition period. We should be able to handle this
    # https://support.coinbase.com/customer/portal/articles/2982947
    if cb_name == 'MCDAI':
        return A_DAI.resolve_to_asset_with_oracles()
    if cb_name == 'DAI':
        # If it's dai and it's queried from the exchange before the end of the upgrade
        if not time:
            time = ts_now()
        if time < COINBASE_DAI_UPGRADE_END_TS:
            # Then it should be the single collateral version
            return A_SAI.resolve_to_asset_with_oracles()
        return A_DAI.resolve_to_asset_with_oracles()

    if not isinstance(cb_name, str):
        raise DeserializationError(f'Got non-string type {type(cb_name)} for coinbase asset')

    name = COINBASE_TO_WORLD.get(cb_name, cb_name)
    return symbol_to_asset_or_token(name)


def asset_from_kucoin(kucoin_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(kucoin_name, str):
        raise DeserializationError(f'Got non-string type {type(kucoin_name)} for kucoin asset')

    if kucoin_name in UNSUPPORTED_KUCOIN_ASSETS:
        raise UnsupportedAsset(kucoin_name)

    name = KUCOIN_TO_WORLD.get(kucoin_name, kucoin_name)
    return symbol_to_asset_or_token(name)


def asset_from_gemini(symbol: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(symbol, str):
        raise DeserializationError(f'Got non-string type {type(symbol)} for gemini asset')

    if symbol in UNSUPPORTED_GEMINI_ASSETS:
        raise UnsupportedAsset(symbol)

    name = GEMINI_TO_WORLD.get(symbol, symbol)
    return symbol_to_asset_or_token(name)


def asset_from_blockfi(symbol: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnknownAsset
    """
    if not isinstance(symbol, str):
        raise DeserializationError(f'Got non-string type {type(symbol)} for blockfi asset')

    symbol = symbol.upper()
    name = BLOCKFI_TO_WORLD.get(symbol, symbol)
    return symbol_to_asset_or_token(name)


def asset_from_iconomi(symbol: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(symbol, str):
        raise DeserializationError(f'Got non-string type {type(symbol)} for iconomi asset')
    symbol = symbol.upper()
    if symbol in UNSUPPORTED_ICONOMI_ASSETS:
        raise UnsupportedAsset(symbol)
    name = ICONOMI_TO_WORLD.get(symbol, symbol)
    return symbol_to_asset_or_token(name)


def asset_from_uphold(symbol: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(symbol, str):
        raise DeserializationError(f'Got non-string type {type(symbol)} for uphold asset')

    name = UPHOLD_TO_WORLD.get(symbol, symbol)
    return symbol_to_asset_or_token(name)


def asset_from_nexo(nexo_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(nexo_name, str):
        raise DeserializationError(f'Got non-string type {type(nexo_name)} for nexo asset')

    our_name = NEXO_TO_WORLD.get(nexo_name, nexo_name)
    return symbol_to_asset_or_token(our_name)


def asset_from_bitpanda(bitpanda_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(bitpanda_name, str):
        raise DeserializationError(f'Got non-string type {type(bitpanda_name)} for bitpanda asset')

    our_name = BITPANDA_TO_WORLD.get(bitpanda_name, bitpanda_name)
    return symbol_to_asset_or_token(our_name)


def asset_from_cryptocom(cryptocom_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(cryptocom_name, str):
        raise DeserializationError(
            f'Got non-string type {type(cryptocom_name)} for cryptocom asset',
        )

    symbol = CRYPTOCOM_TO_WORLD.get(cryptocom_name, cryptocom_name)
    return symbol_to_asset_or_token(symbol)


def asset_from_okx(okx_name: str) -> AssetWithOracles:
    """May raise:
    - DeserializationError
    - UnsupportedAsset
    - UnknownAsset
    """
    if not isinstance(okx_name, str):
        raise DeserializationError(f'Got non-string type {type(okx_name)} for okx asset')

    if okx_name in UNSUPPORTED_OKX_ASSETS:
        raise UnsupportedAsset(okx_name)

    name = OKX_TO_WORLD.get(okx_name, okx_name)
    return symbol_to_asset_or_token(name)


LOCATION_TO_ASSET_MAPPING: dict[Location, Callable[[str], AssetWithOracles]] = {
    Location.BINANCE: asset_from_binance,
    Location.CRYPTOCOM: asset_from_cryptocom,
    Location.BITPANDA: asset_from_bitpanda,
    Location.COINBASEPRO: asset_from_coinbasepro,
    Location.KRAKEN: asset_from_kraken,
    Location.BITSTAMP: asset_from_bitstamp,
    Location.GEMINI: asset_from_gemini,
    Location.POLONIEX: asset_from_poloniex,
    Location.NEXO: asset_from_nexo,
    Location.KUCOIN: asset_from_kucoin,
    Location.OKX: asset_from_okx,
}
