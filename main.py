from colorama import Fore, Back, init
from pycoingecko import CoinGeckoAPI
from forex_python.converter import CurrencyCodes
from dotenv import find_dotenv, load_dotenv
import os
import datetime
from time import sleep
import requests
import shutil

currency_codes = CurrencyCodes()
load_dotenv(find_dotenv())
CURRENCY = os.environ.get("CURRENCY")
Address = os.environ.get("ADDRESS")
poolapi = os.environ.get("POOLAPI")
init(autoreset=True)

def fetchprice():
    cg = CoinGeckoAPI()
    data = cg.get_price(ids="verus-coin", vs_currencies=CURRENCY)
    return data['verus-coin'][CURRENCY]

def fetchpricechanges():
    cg = CoinGeckoAPI()
    data = cg.get_price(ids="verus-coin", vs_currencies=CURRENCY, include_24hr_change=True)
    return data['verus-coin'][f"{CURRENCY}_24h_change"]

def fetchminerstats():
    response = requests.get(f"{poolapi}/miner/{Address}", timeout=100000)
    hashratestring = response.json()['hashrateString']
    estimated_luck = response.json()['estimatedLuck']
    efficiency = response.json()['efficiency']
    current_peak_diff = f"{response.json()['currDiff']} / {response.json()['peakDiff']}"
    avgsharetime = response.json()['avgShareTime']
    stratumServer = response.json()['stratumServer']
    immaturebalance = response.json()['immature']
    maturebalance = response.json()['balance']
    total_paid = response.json()['paid']
    metadata = response.json() 
    return hashratestring, estimated_luck, efficiency, current_peak_diff, avgsharetime, stratumServer, immaturebalance, maturebalance, total_paid, metadata

def fetchworkerstats(metadata):
    # Extract the worker names
    workerlist = [worker.split(':')[0] for worker in metadata['workers']]
    
    # Initialize a list to store worker stats
    worker_stats = []

    # Loop through each worker and fetch their stats
    for workername in workerlist:
        response = requests.get(f"{poolapi}/worker/{Address}.{workername}", timeout=100000)
        worker_data = response.json()
        
        # Check if the hashrateString is "0.00 H"
        if worker_data["hashrateString"] != "0.00 H":
            # Extract and store only the specified elements
            filtered_worker_data = {
                "worker": worker_data["worker"],
                "hashrateString": worker_data["hashrateString"],
                "estimatedLuck": worker_data["estimatedLuck"],
                "efficiency": worker_data["efficiency"],
                "currDiff": worker_data["currDiff"],
                "peakDiff": worker_data["peakDiff"],
                "avgShareTime": worker_data["avgShareTime"],
                "stratumServer": worker_data["stratumServer"]
            }
            worker_stats.append(filtered_worker_data)

    return worker_stats

def main():
    while True:
        overall_hashrate, overall_luck, overall_efficiency, overall_currentpeakdiff, overall_avgsharetime, overall_server, immaturebalance, maturebalance, paidamt, metadata = fetchminerstats()
        os.system('cls' if os.name == 'nt' else 'clear')
        if overall_server == "na":
            expansion = "North America"
        elif overall_server == "eu":
            expansion = "Europe"
        elif overall_server == "ap":
            expansion = "Asia Pacific"
        price = fetchprice()
        pricechanges = fetchpricechanges()
        SYSTEM = (Back.YELLOW + "SYSTEM")
        POOL_API = (Back.MAGENTA + "POOL-API")
        RPI = (Back.CYAN + "RPI")
        HIGH_TEMPS = (Fore.RED + "80.79 C")
        LOW_TEMPS = (Fore.GREEN + "52.34 C")
        print("----------------------------------------------------------------------------------------------------------------")
        columns = shutil.get_terminal_size().columns
        print("Miner Report & Statistics (Updates every 5 mins)".center(columns))
        print("")
        print(SYSTEM, "Worker Results:")
        workers = fetchworkerstats(metadata)
        for worker in workers:
            if worker['stratumServer'] == "na":
                expansion = "North America"
            elif worker['stratumServer'] == "eu":
                expansion = "Europe"
            elif worker['stratumServer'] == "ap":
                expansion = "Asia Pacific"
            print(POOL_API, Fore.BLUE + "Worker:", Fore.GREEN + f"{str(worker['worker']).split('.')[1]}")
            print(POOL_API, Fore.BLUE + "Hashrate:",Fore.GREEN + str(worker['hashrateString']))
            print(POOL_API, Fore.BLUE + "Estimated Luck:",Fore.GREEN + str(worker['estimatedLuck']))
            print(POOL_API, Fore.BLUE + "Efficiency:",Fore.GREEN + str(worker['efficiency']))
            print(POOL_API, Fore.BLUE + "Current Difficulty:",Fore.GREEN + str(worker['currDiff']))
            print(POOL_API, Fore.BLUE + "Peak Difficulty:",Fore.GREEN + str(worker['peakDiff']))
            print(POOL_API, Fore.BLUE + "Average Share Time:",Fore.GREEN + str(worker['avgShareTime']))
            print(POOL_API, Fore.BLUE + "Stratum Server:",Fore.GREEN + f"{str(worker['stratumServer'])} ({expansion})")
            print("")
        print("")
        print(SYSTEM, Fore.GREEN + datetime.datetime.now().strftime("%I:%M %p"))
        print(SYSTEM, Fore.CYAN + "VerusCoin Price:", Fore.GREEN + f"{price} {str(CURRENCY).upper()}")
        print(SYSTEM, Fore.CYAN + "24 Hour Price Change:", Fore.GREEN + f"{round(pricechanges, 2)}%")
        print(SYSTEM, "Overall Pool Results:")
        print(POOL_API, Fore.BLUE + "Overall Hashrate:",Fore.GREEN + overall_hashrate)
        print(POOL_API, Fore.BLUE + "Overall Estimated Luck:",Fore.GREEN + overall_luck)
        print(POOL_API, Fore.BLUE + "Overall Efficiency:",Fore.GREEN + str(overall_efficiency))
        print(POOL_API, Fore.BLUE + "Current VS Peak Difficulty:",Fore.GREEN + str(overall_currentpeakdiff))
        print(POOL_API, Fore.BLUE + "Overall Average Share Time:",Fore.GREEN + str(overall_avgsharetime))
        print(POOL_API, Fore.BLUE + "Stratum Server:",Fore.GREEN + f"{str(overall_server)} ({expansion})")
        print(POOL_API, Fore.BLUE + "Immature Balance:",Fore.GREEN + f"{str(immaturebalance)} VRSC or {immaturebalance * price} {str(CURRENCY).upper()}")
        print(POOL_API, Fore.BLUE + "Mature Balance:",Fore.GREEN + f"{str(maturebalance)} VRSC or {maturebalance * price} {str(CURRENCY).upper()}")
        print(POOL_API, Fore.BLUE + "Total Paid Amount:",Fore.GREEN + f"{str(paidamt)} VRSC or {paidamt * price} {str(CURRENCY).upper()}")
        print("")
        print(RPI, Fore.WHITE + f"Overall temperatures measured is about " + HIGH_TEMPS, Fore.WHITE + "when the RPIs are at full load.")
        print(RPI, Fore.WHITE + "About", LOW_TEMPS, Fore.WHITE + "when the RPIs are at rest..")
        print(SYSTEM, "Sleeping for 5 mins...")
        sleep(300)

main()
