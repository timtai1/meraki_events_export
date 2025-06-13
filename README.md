# meraki_events_export

Why we need this script to export event logs from Meraki Dashboard?
When we visit Meraki Dashboard, we can see the event logs, but when exporting the logs from the portal, it will only export the logs within one month, and with 1000 records limitation, which is NOT user frendly.

This script is updated from https://github.com/itris-one/meraki-eventlog-export, as that one is outdated. 

You will need following modules:

```
requests
python-dateutil
```

### Creating an API-Key
Login to the meraki dashboard, klick on your username and on My Profile. Create a key in the "API Access" category.

Further information in the [meraki API documentation](https://documentation.meraki.com/General_Administration/Other_Topics/The_Cisco_Meraki_Dashboard_API)

### Getting the network-id

Go to the [get-organizations rest api doc](https://developer.cisco.com/meraki/api/#!get-organizations), click on Configuration and replace the API-Key with yours. Run the get organizations api call and copy your (organization) id from the response data.

Switchover to [get-organizations-networks rest api doc](https://developer.cisco.com/meraki/api/#!get-organization-networks), paste your organization ID and run the request. You will find your network id in the response data as 'id' parameter.

Or, you can just login to Meraki Dashboard and use developer tools to find network ID.


## How to Use

```
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
  --client ComputerName Filter the clientName
  -v, --verbose         verbose mode
```

## Examples : 
Getting all wireless network events from the DevNet Sandbox as CSV file:
```
$ python meraki_events_export.py -k 40dde28d24ca18dfkb93da1ceefc3xxxxxxxx -n L_5770232973xxxxxxx -c exported_file.csv --client machine_name -v

```
