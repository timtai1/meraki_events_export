# meraki_events_export

This script is updated from https://github.com/itris-one/meraki-eventlog-export, as that one is outdated.

# How to Use
$ python meraki_events.py --help                                                                                     :(
usage: meraki_events.py [-h] [-k API_KEY] -n NETWORK_ID [-p PRODUCT_TYPE] [-j JSON] [-c CSV] [-v]

Small python script for downloading the meraki eventlog. The events are downloaded in reverse starting from now and proceeds until all events are parsed Example: meraki_events.py
-k MERAKI_API_KEY -n MERAKI_NET_ID -c events.csv

options:
  -h, --help            show this help message and exit
  -k API_KEY, --api-key API_KEY
                        Meraki API Key (X-Cisco-Meraki-API-Key). The env variable MERAKI_API_KEY is used if available
  -n NETWORK_ID, --network-id NETWORK_ID
                        Meraki Network ID. The env variable MERAKI_NET_ID is used if available
  -p PRODUCT_TYPE, --product-type PRODUCT_TYPE
                        Product type filter. Valid types are wireless, appliance, switch, systemsManager, camera, and cellularGateway. Defaults to wireless
  -j JSON, --json JSON  Export as json
  -c CSV, --csv CSV     Export es csv
  -v, --verbose         verbose mode
