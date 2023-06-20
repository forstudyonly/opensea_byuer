import asyncio
import json
import os
import time
import pickle
import requests
from aiogram import Bot
from dotenv import load_dotenv
from web3 import Web3
from web3.auto import w3
from core.blur_parser import get_top_bid, get_chromedriver
from core.database.base import bd_all_collections, bd_get_percent, bd_add_ignored, bd_off_ignored
from core.settings import settings
from core.handlers.basic import find_buy_nft

load_dotenv()

token = settings.bots.bot_token
bot = Bot(token=token)

proxy_data = {
        "http": f"",
        "https": f""
}

my_address = os.getenv('MY_ADDRESS')
private_key = os.getenv('PRIVATE_KEY')

api_key_opensea = os.getenv("API_KEY_OPENSEA")

all_listings_url = "https://api.opensea.io/v2/listings/collection/{slug}/all?limit=100&next={next}"
retrieve_listing_url = "https://api.opensea.io/v2/orders/ethereum/seaport/listings?asset_contract_address={asset_contract_address}&limit=50&token_ids={token_ids}&order_by=eth_price&order_direction=asc"

main_rpc_url = 'https://mainnet.infura.io/v3/b406bcc739ad4f118d1ed4f01d283567'


headers = {
        'X-API-KEY': api_key_opensea,
        'content-type': 'application/json',
}
# proxies
with open("proxy_http_ip.txt", "r", encoding="utf-8") as file:
    proxies = file.read().split("\n")

num_proxy = 0
# значения next для всех коллекций что бы сразу получать последние обновленияв листинге
with open("assets/dict_next_values.data", "rb") as file:
    dict_of_next_values = pickle.load(file)


def update_proxy():
    global num_proxy, proxies, proxy_data
    num_proxy += 1
    if num_proxy >= len(proxies):
        num_proxy = 0
    proxy_data['http'] = f"http://{proxies[num_proxy]}"
    proxy_data['https'] = f"http://{proxies[num_proxy]}"


def get_all_listings(slug):
    global api_key_value
    if dict_of_next_values.get(slug, False):
        next_value = dict_of_next_values.get(slug)
    else:
        next_value = "start"
    str_num = 1
    count_requests = 0
    while next_value:
        count_requests += 1
        if next_value == "start":
            next_value = ""
        url = all_listings_url.format(slug=slug, next=next_value)
        try:
            update_proxy()
            with requests.Session() as s:
                s.proxies = proxy_data
                response = s.get(url, headers=headers, timeout=2)
        except Exception as ex:
            with open("assets/invalid_proxy.txt", "a", encoding="utf-8") as file_proxy:
                file_proxy.write(f"Нерабочая прокси {proxy_data['http']}\n")
            return False, ""
        if response.status_code == 200:
            if "Request was throttled" in response.text:
                time.sleep(1)
                continue
            orders = json.loads(response.text)['listings']
            next_value = json.loads(response.text)['next']
            if next_value:
                dict_of_next_values[slug] = next_value

            if not orders and str_num == 1:
                dict_of_next_values[slug] = "start"
                return False, ""
            if str_num == 1:
                min_order = orders[0]

            for i, order in enumerate(orders):
                if int(order['price']['current']['value']) <= int(min_order['price']['current']['value']):
                    min_order = order
                else:
                    continue

            str_num += 1
        elif response.status_code == 500:
            next_value = "start"
            dict_of_next_values[slug] = next_value
            time.sleep(1)
            continue
        else:
            time.sleep(1)
            continue
    chain = min_order['chain']
    order_hash = min_order['order_hash']
    protocol_address = min_order['protocol_address']
    contract_address = min_order['protocol_data']['parameters']['offer'][0]['token']
    token_ids = min_order['protocol_data']['parameters']['offer'][0]['identifierOrCriteria']
    price_value = int(min_order['price']['current']['value'])

    return chain, order_hash, protocol_address, contract_address, token_ids, price_value


def get_needed_info(chain, order_hash, protocol_address, contract_address, token_ids):
    json_data = {
        "offer": {
            "hash": order_hash,
            "chain": chain,
            "protocol_address": protocol_address
        },
        "fulfiller": {
                "address": my_address
        },
        "consideration": {
            "asset_contract_address": contract_address,
            "token_id": token_ids
        }
    }
    count = 0
    while count < 7:
        with requests.Session() as s:
            s.proxies = proxy_data
            response = s.post('https://api.opensea.io/v2/offers/fulfillment_data', headers=headers, json=json_data)

        if response.status_code == 200:
            if "Request was throttled" in response.text:
                time.sleep(1)
                count += 1
                continue
            return True, response.text
        else:
            count += 1
            time.sleep(1)
            continue
    return False, ""


def buy_nft(json_data, price, top_bid_wei):
    contract_abi = json.loads('[{"inputs":[{"internalType":"address","name":"conduitController","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"BadContractSignature","type":"error"},{"inputs":[],"name":"BadFraction","type":"error"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"BadReturnValueFromERC20OnTransfer","type":"error"},{"inputs":[{"internalType":"uint8","name":"v","type":"uint8"}],"name":"BadSignatureV","type":"error"},{"inputs":[],"name":"CannotCancelOrder","type":"error"},{"inputs":[],"name":"ConsiderationCriteriaResolverOutOfRange","type":"error"},{"inputs":[],"name":"ConsiderationLengthNotEqualToTotalOriginal","type":"error"},{"inputs":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"considerationIndex","type":"uint256"},{"internalType":"uint256","name":"shortfallAmount","type":"uint256"}],"name":"ConsiderationNotMet","type":"error"},{"inputs":[],"name":"CriteriaNotEnabledForItem","type":"error"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256[]","name":"identifiers","type":"uint256[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"name":"ERC1155BatchTransferGenericFailure","type":"error"},{"inputs":[],"name":"InexactFraction","type":"error"},{"inputs":[],"name":"InsufficientNativeTokensSupplied","type":"error"},{"inputs":[],"name":"Invalid1155BatchTransferEncoding","type":"error"},{"inputs":[],"name":"InvalidBasicOrderParameterEncoding","type":"error"},{"inputs":[{"internalType":"address","name":"conduit","type":"address"}],"name":"InvalidCallToConduit","type":"error"},{"inputs":[{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"address","name":"conduit","type":"address"}],"name":"InvalidConduit","type":"error"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"InvalidContractOrder","type":"error"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"InvalidERC721TransferAmount","type":"error"},{"inputs":[],"name":"InvalidFulfillmentComponentData","type":"error"},{"inputs":[{"internalType":"uint256","name":"value","type":"uint256"}],"name":"InvalidMsgValue","type":"error"},{"inputs":[],"name":"InvalidNativeOfferItem","type":"error"},{"inputs":[],"name":"InvalidProof","type":"error"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"InvalidRestrictedOrder","type":"error"},{"inputs":[],"name":"InvalidSignature","type":"error"},{"inputs":[],"name":"InvalidSigner","type":"error"},{"inputs":[{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"}],"name":"InvalidTime","type":"error"},{"inputs":[{"internalType":"uint256","name":"fulfillmentIndex","type":"uint256"}],"name":"MismatchedFulfillmentOfferAndConsiderationComponents","type":"error"},{"inputs":[{"internalType":"enum Side","name":"side","type":"uint8"}],"name":"MissingFulfillmentComponentOnAggregation","type":"error"},{"inputs":[],"name":"MissingItemAmount","type":"error"},{"inputs":[],"name":"MissingOriginalConsiderationItems","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"NativeTokenTransferGenericFailure","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"NoContract","type":"error"},{"inputs":[],"name":"NoReentrantCalls","type":"error"},{"inputs":[],"name":"NoSpecifiedOrdersAvailable","type":"error"},{"inputs":[],"name":"OfferAndConsiderationRequiredOnFulfillment","type":"error"},{"inputs":[],"name":"OfferCriteriaResolverOutOfRange","type":"error"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"OrderAlreadyFilled","type":"error"},{"inputs":[{"internalType":"enum Side","name":"side","type":"uint8"}],"name":"OrderCriteriaResolverOutOfRange","type":"error"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"OrderIsCancelled","type":"error"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"OrderPartiallyFilled","type":"error"},{"inputs":[],"name":"PartialFillsNotEnabledForOrder","type":"error"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"TokenTransferGenericFailure","type":"error"},{"inputs":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"considerationIndex","type":"uint256"}],"name":"UnresolvedConsiderationCriteria","type":"error"},{"inputs":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"offerIndex","type":"uint256"}],"name":"UnresolvedOfferCriteria","type":"error"},{"inputs":[],"name":"UnusedItemParameters","type":"error"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"newCounter","type":"uint256"},{"indexed":true,"internalType":"address","name":"offerer","type":"address"}],"name":"CounterIncremented","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"offerer","type":"address"},{"indexed":true,"internalType":"address","name":"zone","type":"address"}],"name":"OrderCancelled","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"indexed":true,"internalType":"address","name":"offerer","type":"address"},{"indexed":true,"internalType":"address","name":"zone","type":"address"},{"indexed":false,"internalType":"address","name":"recipient","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"}],"indexed":false,"internalType":"struct SpentItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"indexed":false,"internalType":"struct ReceivedItem[]","name":"consideration","type":"tuple[]"}],"name":"OrderFulfilled","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"orderHash","type":"bytes32"},{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"indexed":false,"internalType":"struct OrderParameters","name":"orderParameters","type":"tuple"}],"name":"OrderValidated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32[]","name":"orderHashes","type":"bytes32[]"}],"name":"OrdersMatched","type":"event"},{"inputs":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"counter","type":"uint256"}],"internalType":"struct OrderComponents[]","name":"orders","type":"tuple[]"}],"name":"cancel","outputs":[{"internalType":"bool","name":"cancelled","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"uint120","name":"numerator","type":"uint120"},{"internalType":"uint120","name":"denominator","type":"uint120"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes","name":"extraData","type":"bytes"}],"internalType":"struct AdvancedOrder","name":"","type":"tuple"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"enum Side","name":"side","type":"uint8"},{"internalType":"uint256","name":"index","type":"uint256"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"bytes32[]","name":"criteriaProof","type":"bytes32[]"}],"internalType":"struct CriteriaResolver[]","name":"","type":"tuple[]"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"},{"internalType":"address","name":"recipient","type":"address"}],"name":"fulfillAdvancedOrder","outputs":[{"internalType":"bool","name":"fulfilled","type":"bool"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"uint120","name":"numerator","type":"uint120"},{"internalType":"uint120","name":"denominator","type":"uint120"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes","name":"extraData","type":"bytes"}],"internalType":"struct AdvancedOrder[]","name":"","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"enum Side","name":"side","type":"uint8"},{"internalType":"uint256","name":"index","type":"uint256"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"bytes32[]","name":"criteriaProof","type":"bytes32[]"}],"internalType":"struct CriteriaResolver[]","name":"","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[][]","name":"","type":"tuple[][]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[][]","name":"","type":"tuple[][]"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"},{"internalType":"address","name":"recipient","type":"address"},{"internalType":"uint256","name":"maximumFulfilled","type":"uint256"}],"name":"fulfillAvailableAdvancedOrders","outputs":[{"internalType":"bool[]","name":"","type":"bool[]"},{"components":[{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ReceivedItem","name":"item","type":"tuple"},{"internalType":"address","name":"offerer","type":"address"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"}],"internalType":"struct Execution[]","name":"","type":"tuple[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct Order[]","name":"","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[][]","name":"","type":"tuple[][]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[][]","name":"","type":"tuple[][]"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"},{"internalType":"uint256","name":"maximumFulfilled","type":"uint256"}],"name":"fulfillAvailableOrders","outputs":[{"internalType":"bool[]","name":"","type":"bool[]"},{"components":[{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ReceivedItem","name":"item","type":"tuple"},{"internalType":"address","name":"offerer","type":"address"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"}],"internalType":"struct Execution[]","name":"","type":"tuple[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"considerationToken","type":"address"},{"internalType":"uint256","name":"considerationIdentifier","type":"uint256"},{"internalType":"uint256","name":"considerationAmount","type":"uint256"},{"internalType":"address payable","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"internalType":"address","name":"offerToken","type":"address"},{"internalType":"uint256","name":"offerIdentifier","type":"uint256"},{"internalType":"uint256","name":"offerAmount","type":"uint256"},{"internalType":"enum BasicOrderType","name":"basicOrderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"offererConduitKey","type":"bytes32"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalAdditionalRecipients","type":"uint256"},{"components":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct AdditionalRecipient[]","name":"additionalRecipients","type":"tuple[]"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct BasicOrderParameters","name":"parameters","type":"tuple"}],"name":"fulfillBasicOrder","outputs":[{"internalType":"bool","name":"fulfilled","type":"bool"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"considerationToken","type":"address"},{"internalType":"uint256","name":"considerationIdentifier","type":"uint256"},{"internalType":"uint256","name":"considerationAmount","type":"uint256"},{"internalType":"address payable","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"internalType":"address","name":"offerToken","type":"address"},{"internalType":"uint256","name":"offerIdentifier","type":"uint256"},{"internalType":"uint256","name":"offerAmount","type":"uint256"},{"internalType":"enum BasicOrderType","name":"basicOrderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"offererConduitKey","type":"bytes32"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalAdditionalRecipients","type":"uint256"},{"components":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct AdditionalRecipient[]","name":"additionalRecipients","type":"tuple[]"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct BasicOrderParameters","name":"parameters","type":"tuple"}],"name":"fulfillBasicOrder_efficient_6GL6yc","outputs":[{"internalType":"bool","name":"fulfilled","type":"bool"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct Order","name":"","type":"tuple"},{"internalType":"bytes32","name":"fulfillerConduitKey","type":"bytes32"}],"name":"fulfillOrder","outputs":[{"internalType":"bool","name":"fulfilled","type":"bool"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"address","name":"contractOfferer","type":"address"}],"name":"getContractOffererNonce","outputs":[{"internalType":"uint256","name":"nonce","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"offerer","type":"address"}],"name":"getCounter","outputs":[{"internalType":"uint256","name":"counter","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"counter","type":"uint256"}],"internalType":"struct OrderComponents","name":"","type":"tuple"}],"name":"getOrderHash","outputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"orderHash","type":"bytes32"}],"name":"getOrderStatus","outputs":[{"internalType":"bool","name":"isValidated","type":"bool"},{"internalType":"bool","name":"isCancelled","type":"bool"},{"internalType":"uint256","name":"totalFilled","type":"uint256"},{"internalType":"uint256","name":"totalSize","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"incrementCounter","outputs":[{"internalType":"uint256","name":"newCounter","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"information","outputs":[{"internalType":"string","name":"version","type":"string"},{"internalType":"bytes32","name":"domainSeparator","type":"bytes32"},{"internalType":"address","name":"conduitController","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"uint120","name":"numerator","type":"uint120"},{"internalType":"uint120","name":"denominator","type":"uint120"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes","name":"extraData","type":"bytes"}],"internalType":"struct AdvancedOrder[]","name":"","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"enum Side","name":"side","type":"uint8"},{"internalType":"uint256","name":"index","type":"uint256"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"bytes32[]","name":"criteriaProof","type":"bytes32[]"}],"internalType":"struct CriteriaResolver[]","name":"","type":"tuple[]"},{"components":[{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[]","name":"offerComponents","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[]","name":"considerationComponents","type":"tuple[]"}],"internalType":"struct Fulfillment[]","name":"","type":"tuple[]"},{"internalType":"address","name":"recipient","type":"address"}],"name":"matchAdvancedOrders","outputs":[{"components":[{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ReceivedItem","name":"item","type":"tuple"},{"internalType":"address","name":"offerer","type":"address"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"}],"internalType":"struct Execution[]","name":"","type":"tuple[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct Order[]","name":"","type":"tuple[]"},{"components":[{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[]","name":"offerComponents","type":"tuple[]"},{"components":[{"internalType":"uint256","name":"orderIndex","type":"uint256"},{"internalType":"uint256","name":"itemIndex","type":"uint256"}],"internalType":"struct FulfillmentComponent[]","name":"considerationComponents","type":"tuple[]"}],"internalType":"struct Fulfillment[]","name":"","type":"tuple[]"}],"name":"matchOrders","outputs":[{"components":[{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifier","type":"uint256"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ReceivedItem","name":"item","type":"tuple"},{"internalType":"address","name":"offerer","type":"address"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"}],"internalType":"struct Execution[]","name":"","type":"tuple[]"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"pure","type":"function"},{"inputs":[{"components":[{"components":[{"internalType":"address","name":"offerer","type":"address"},{"internalType":"address","name":"zone","type":"address"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"}],"internalType":"struct OfferItem[]","name":"offer","type":"tuple[]"},{"components":[{"internalType":"enum ItemType","name":"itemType","type":"uint8"},{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"identifierOrCriteria","type":"uint256"},{"internalType":"uint256","name":"startAmount","type":"uint256"},{"internalType":"uint256","name":"endAmount","type":"uint256"},{"internalType":"address payable","name":"recipient","type":"address"}],"internalType":"struct ConsiderationItem[]","name":"consideration","type":"tuple[]"},{"internalType":"enum OrderType","name":"orderType","type":"uint8"},{"internalType":"uint256","name":"startTime","type":"uint256"},{"internalType":"uint256","name":"endTime","type":"uint256"},{"internalType":"bytes32","name":"zoneHash","type":"bytes32"},{"internalType":"uint256","name":"salt","type":"uint256"},{"internalType":"bytes32","name":"conduitKey","type":"bytes32"},{"internalType":"uint256","name":"totalOriginalConsiderationItems","type":"uint256"}],"internalType":"struct OrderParameters","name":"parameters","type":"tuple"},{"internalType":"bytes","name":"signature","type":"bytes"}],"internalType":"struct Order[]","name":"","type":"tuple[]"}],"name":"validate","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]')

    nft_contract_address = Web3.to_checksum_address('0x00000000000000ADc04C56Bf30aC9d3c0aAF14dC')
    nft_contract = web3.eth.contract(nft_contract_address, abi=contract_abi)

    json_data = json.loads(json_data)

    parameters = json_data['fulfillment_data']['transaction']['input_data']['parameters']
    gas_price = web3.eth.gas_price
    top_bid_price = web3.from_wei(top_bid_wei, 'ether')
    gwei = 1000000000
    if float(top_bid_price) <= 0.1:
        if gas_price <= 80 * gwei:
            pass
        else:
            return False, f"Gas price: {web3.from_wei(gas_price, 'ether')}"
    elif 0.1 <= float(top_bid_price) <= 0.2:
        if gas_price <= 100 * gwei:
            pass
        else:
            return False, f"Gas price: {web3.from_wei(gas_price, 'ether')}"
    elif 0.2 <= float(top_bid_price) <= 0.4:
        if gas_price <= 150 * gwei:
            pass
        else:
            return False, f"Gas price: {web3.from_wei(gas_price, 'ether')}"
    elif float(top_bid_price) > 0.4:
        if gas_price <= 500 * gwei:
            pass
        else:
            return False, f"Gas price: {web3.from_wei(gas_price, 'ether')}"
    gas_price = int(gas_price * 1.3)
    dict_transaction = {
      'chainId': 1,
      'from': Web3.to_checksum_address(my_address),
      'value': price,
      'gasPrice': gas_price,
      'nonce': web3.eth.get_transaction_count(Web3.to_checksum_address(my_address)),
    }
    additional_recipients = []
    if int(parameters['totalOriginalAdditionalRecipients']) > 0:
        for recipient in parameters['additionalRecipients']:
            recip = [int(recipient['amount']), Web3.to_checksum_address(recipient['recipient'])]
            additional_recipients.append(recip)

    try:
        make_order = nft_contract.functions.fulfillBasicOrder(
            (
                Web3.to_checksum_address(parameters['considerationToken']),
                int(parameters['considerationIdentifier']),
                int(parameters['considerationAmount']),
                Web3.to_checksum_address(parameters['offerer']),
                Web3.to_checksum_address(parameters['zone']),
                Web3.to_checksum_address(parameters['offerToken']),
                int(parameters['offerIdentifier']),
                int(parameters['offerAmount']),
                int(parameters['basicOrderType']),
                int(parameters['startTime']),
                int(parameters['endTime']),
                w3.to_bytes(hexstr=parameters['zoneHash']),
                int(parameters['salt']),
                w3.to_bytes(hexstr=parameters['offererConduitKey']),
                w3.to_bytes(hexstr=parameters['fulfillerConduitKey']),
                int(parameters['totalOriginalAdditionalRecipients']),
                additional_recipients,
                parameters['signature']
            )
          ).build_transaction(dict_transaction)
    except BaseException as ex:
        with open("assets/auto_buy_errors.txt", "a", encoding="utf-8") as file:
            file.write(f"{ex}\n{json_data}\n")
        return False, "Произошла ошибка при генерации хэша для транзакции. Подробнее в auto_buy_errors.txt"
    try:
        signed_txn = web3.eth.account.sign_transaction(make_order, private_key)
        txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return True, txn_hash.hex()

    except BaseException as ex:
        with open("assets/auto_buy_errors_signing.txt", "a", encoding="utf-8") as file:
            file.write(f"{ex}\n{json_data}\n")
        return False, "Произошла ошибка при генерации подписи и отправлении транзакции. Подробнее в auto_buy_errors_signing.txt"


if __name__ == "__main__":
    while True:
        try:
            web3 = Web3(Web3.HTTPProvider(main_rpc_url))
            print(f"Is connected: {web3.is_connected()}")
            driver = get_chromedriver()

            if driver:
                while True:
                    time_start = time.time()

                    # названия колекции макс и мин цены для наших коллекций получаем из бд
                    collections = bd_all_collections()
                    # получаем процент разницы от top bid
                    percent = bd_get_percent()
                    percent = int(percent.strip()) / 100

                    for col_info in collections:
                        if int(col_info[-2]) == 1:
                            if time.time() > float(col_info[-1]):
                                bd_off_ignored(col_info[1])
                                pass
                            else:
                                continue
                        slug = col_info[1].strip()

                        order_values = get_all_listings(slug)
                        # проверить по параметрам и купить с оповещением в тг затем добавить в игнорирование коллекцию что бы больше не покупать сутки
                        if order_values[0]:
                            min_price = Web3.to_wei(float(col_info[2].strip().replace(",", ".")), "ether")
                            max_price = Web3.to_wei(float(col_info[3].strip().replace(",", ".")), "ether")
                            if min_price <= int(order_values[-1]) <= max_price:
                                top_bid = get_top_bid(driver, slug)
                                if top_bid:
                                    top_bid = web3.to_wei(float(top_bid), "ether")
                                    # чекаем в blur top bid  сравниваем с процентом и если проходит, покупаем нфт и заносим в игнорируемые кол-ции
                                    if int(order_values[-1]) <= top_bid * (1-percent):
                                        fullfill_order = get_needed_info(order_values[0], order_values[1], order_values[2], order_values[3], order_values[4])
                                        if fullfill_order[0]:
                                            res_of_buy = [True, "test"]
                                            if res_of_buy[0]:
                                                # вызываем отправление сообщения в группу тг и игнорируем кол-цию
                                                info = [slug, web3.from_wei(int(order_values[-1]), 'ether'), web3.from_wei(int(top_bid), 'ether'), res_of_buy[1]]

                                                asyncio.get_event_loop().run_until_complete(find_buy_nft(bot, info))
                                                bd_add_ignored(slug, int(time.time() + 24*60*60))

                                            else:
                                                # отправляем в тг всю инфу и пишем что не получилось купить и игнорируем данную нфт
                                                info = [slug, web3.from_wei(int(order_values[-1]), 'ether'), web3.from_wei(int(top_bid), 'ether'), res_of_buy[1], False]

                                                asyncio.get_event_loop().run_until_complete(find_buy_nft(bot, info))
                                                bd_add_ignored(slug, int(time.time() + 24 * 60 * 60))

                    with open("assets/dict_next_values.data", "wb") as file:
                        pickle.dump(dict_of_next_values, file)
                    print(f"Заняло времени: {time.time() - time_start}")
        except Exception as ex:
            with open("assets/crash_errors.txt", "a", encoding="utf-8") as file:
                file.write(f"\n{ex}\n")
            try:
                driver.quit()
            except Exception as ex:
                pass
            continue
