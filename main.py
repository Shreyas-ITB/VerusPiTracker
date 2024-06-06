import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime
from time import sleep
import requests
import shutil
from pythonping import ping
from colorama import Fore, Back, init
from pycoingecko import CoinGeckoAPI
from forex_python.converter import CurrencyCodes
from dotenv import find_dotenv, load_dotenv

currency_codes = CurrencyCodes()
load_dotenv(find_dotenv())
CURRENCY = os.environ.get("CURRENCY")
Address = os.environ.get("ADDRESS")
poolapi = os.environ.get("POOLAPI")
onTABLET = os.environ.get("onTABLET")
init(autoreset=True)

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            json_data = json.loads(post_data)
            filename = f"system_info_{json_data['name']}.json"
            with open(filename, 'w') as f:
                json.dump(json_data, f)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Data received and saved.")
        except json.JSONDecodeError as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON data.")
            print(Fore.RED + f"Error decoding JSON: {e}")
            print(Fore.RED + f"Received data: {post_data}")

def start_socket_server():
    server_address = ('', 5000)
    httpd = HTTPServer(server_address, RequestHandler)
    print("Socket server started, waiting for connections...")
    httpd.serve_forever()

def ping_device(ip):
    try:
        result = ping(ip, count=5)  # Ping the device 5 times
        avg_rtt_ms = result.rtt_avg_ms
        return avg_rtt_ms
    except Exception as e:
        return None

def check_online(ip):
    try:
        result = ping(ip, count=1)  # Ping the device once
        return result.success()
    except Exception as e:
        return False

def get_ip(username):
    return os.environ.get(username + "_IP")

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

def collect_rpi_data():
    data = []
    for filename in os.listdir('.'):
        if filename.startswith('system_info_') and filename.endswith('.json'):
            with open(filename, 'r') as f:
                try:
                    data.append(json.load(f))
                except json.JSONDecodeError as e:
                    print(Fore.RED + f"Error decoding JSON from file {filename}: {e}")
    return data

def bytes_to_human_readable(bytes):
    if bytes < 1024:
        return f"{bytes} bytes (b/s)"
    elif bytes < 1024 ** 2:
        return f"{bytes / 1024:.2f} KB/s"
    elif bytes < 1024 ** 3:
        return f"{bytes / (1024 ** 2):.2f} MB/s"
    else:
        return f"{bytes / (1024 ** 3):.2f} GB/s"

def main():
    threading.Thread(target=start_socket_server, daemon=True).start()

    while True:
        try:
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
            
            # Collect data from all RPI JSON files
            rpi_data = collect_rpi_data()
            print(RPI, "Raspberry Pi SBC Data Logger:")
            for device in rpi_data:
                temp_color = Fore.RED if float(device['temp']) > 60 else Fore.GREEN
                netcons_hr = bytes_to_human_readable(int(device['netcons']))
                if onTABLET == "False" or onTABLET == "false":
                    ip_address = get_ip(str(device['name']))
                    if ip_address:
                        online_status = check_online(ip_address)
                        if online_status:
                            avg_rtt_ms = ping_device(ip_address)
                            if avg_rtt_ms is not None:
                                print(RPI, Fore.WHITE + f"{device['name']}", Fore.WHITE + "is running at a temperature of:", temp_color + f"{device['temp']} C", Fore.WHITE + "Net Speed:", Fore.BLUE + f"{netcons_hr}", Fore.WHITE + "Online:", Fore.GREEN + "True", Fore.WHITE + "Avg RTT:", Fore.BLUE + f"{avg_rtt_ms:.2f} ms")
                            else:
                                print(RPI, Fore.WHITE + f"{device['name']}", Fore.WHITE + "last updated temperature is:", temp_color + f"{device['temp']} C", Fore.WHITE + "last updated Net Speed:", Fore.BLUE + f"{netcons_hr}", Fore.WHITE + "Online:", Fore.RED + "False")
                        else:
                            print(RPI, Fore.WHITE + f"{device['name']}", Fore.WHITE + "last updated temperature is:", temp_color + f"{device['temp']} C", Fore.WHITE + "last updated Net Speed:", Fore.BLUE + f"{netcons_hr}", Fore.WHITE + "Online:", Fore.RED + "False")
                    else:
                        print(SYSTEM, Fore.RED + "Unable to get IP address for", device['name'])
                elif onTABLET == "True" or onTABLET == "true":
                    print(RPI, Fore.WHITE + f"{device['name']}", Fore.WHITE + "is running at a temperature of:", temp_color + f"{device['temp']} C", Fore.WHITE + "Net Speed:", Fore.BLUE + f"{netcons_hr}")
                else:
                    print(SYSTEM, Fore.RED + "Invalid onTABLET value. Please set it to True or False.")
            print(SYSTEM, "Sleeping for 5 mins...")
            sleep(300)
        except Exception as e:
            print(Fore.RED + "An error occurred: ", str(e), Fore.GREEN + "Retrying in 30 seconds...")
            sleep(30)

if __name__ == "__main__":
    main()
