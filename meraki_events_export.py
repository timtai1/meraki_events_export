import logging as log
import json
import requests
import csv
import time
import argparse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
import dateutil.parser

PAGE_SIZE = 1000

def readPage(re, baseURL, endingBefore=None, pageSize=1000, **params):
    """Helper function for handling HTTP retries and pagination parameters"""
    params["perPage"] = pageSize
    if endingBefore:
        params["endingBefore"] = endingBefore

    try:
        response = re.get(baseURL, params=params)
    except requests.exceptions.ConnectionError:
        log.warning("Connection error, retrying in 10 seconds")
        time.sleep(10)
        return readPage(re, baseURL, pageSize=pageSize, **params)    

    if response.status_code == 200:
        page = response.json()
        return page["events"], page['pageStartAt'], page['pageEndAt'], len(page["events"]) == pageSize

    elif response.status_code == 429:
        log.warning("API rate limit reached, waiting %s seconds" % response.headers["Retry-After"])
        time.sleep(int(response.headers["Retry-After"]))
        return readPage(re, baseURL, pageSize=pageSize, **params)
  
    elif response.status_code == 404: # Eventlog is empty
        log.error("Invalid network-id")
        exit(1)
    elif response.status_code == 401:
        log.error("Authentication failed, please check if the API key is correct")
        exit(1)
    else:
        log.error("Unhandled status code %s" % (response.status_code))
        exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python script to download Meraki eventlog for one year. Events are downloaded in reverse starting from now until one year ago. Example: meraki_events2.py -k MERAKI_API_KEY -n MERAKI_NET_ID -c events.csv --client COMPUTER_NAME")

    parser.add_argument('-k', '--api-key', help='Meraki API Key (X-Cisco-Meraki-API-Key). Uses environment variable MERAKI_API_KEY if available',
                        default=os.environ.get("MERAKI_API_KEY"), required=os.environ.get("MERAKI_API_KEY") is None)
  
    parser.add_argument('-n', '--network-id', help='Meraki Network ID. Uses environment variable MERAKI_NET_ID if available',
                        default=os.environ.get("MERAKI_NET_ID"), required=os.environ.get("MERAKI_NET_ID") is None)
  
    parser.add_argument('-p', '--product-type', help='Product type filter. Valid types: wireless, appliance, switch, systemsManager, camera, cellularGateway. Defaults to wireless', default="wireless")
  
    parser.add_argument('-c', '--csv', help='Export events as CSV file')
    parser.add_argument('-j', '--json', help='Export events as JSON file')
    parser.add_argument('--client', help='Filter events by client name (computer name)', default=None)
    parser.add_argument('-v', '--verbose', action='store_const', const=True, help='Enable verbose logging')
    
    args = parser.parse_args()
  
    re = requests.Session()
    re.headers['X-Cisco-Meraki-API-Key'] = args.api_key

    retries = Retry(total=5, backoff_factor=5, status_forcelist=[502, 503, 504])
    re.mount('http://', HTTPAdapter(max_retries=retries))

    if args.verbose:
        log.basicConfig(level=log.DEBUG)
        
    if not args.json and not args.csv:
        parser.print_help()
        print("\nAt least one export format (JSON or CSV) is required\n")
        exit(1)

    # Calculate cutoff time (one year ago from now)
    cutoff_time = datetime.now().astimezone() - relativedelta(years=1)
    log.debug("Cutoff time for events: %s" % cutoff_time.isoformat())

    startAt = None
    fullPage = True
    pageNum = 0
    last_event_time = None
  
    neJSON = None
  
    if args.json:
        neJSON = open(args.json, "w")

    neCSV = None
    neCSVwriter = None
  
    # Define fixed field order: occurredAt, deviceName, ssidName, clientDescription, others, eventData
    fixed_fields = ["occurredAt", "deviceName", "ssidName", "clientDescription"]
    dynamic_fields = set([
        "networkId", "type", "description", "clientId", "deviceSerial",
        "ssidNumber", "clientMac", "category", "clientName"
    ])
    fieldnames = fixed_fields + list(dynamic_fields) + ["eventData"]

    if args.csv:
        neCSV = open(args.csv, "w", newline='')
        neCSVwriter = csv.DictWriter(neCSV, fieldnames=fieldnames)
        neCSVwriter.writeheader()

    eventCount = 0

    try:
        while fullPage or (last_event_time and last_event_time > cutoff_time):
            pageNum += 1
            print("Requesting page %s (before %s)" % (pageNum, startAt))
            
            # Build API request parameters, including client filter
            params = {"productType": args.product_type}
            if args.client:
                params["clientName"] = args.client  # Filter by clientName
                log.debug("Filtering events by clientName: %s" % args.client)

            pageEvents, startAt, endAt, fullPage = readPage(re, "https://api.meraki.com/api/v1/networks/%s/events" % args.network_id, pageSize=PAGE_SIZE, endingBefore=startAt, **params)

            # If no events are returned, stop fetching
            if not pageEvents:
                print("No more events found, stopping")
                break

            # Update dynamic fields with any new fields found in events
            for event in pageEvents:
                dynamic_fields.update([k for k in event.keys() if k not in fixed_fields and k != "eventData"])

            # Update fieldnames if new fields are found
            new_fieldnames = fixed_fields + [f for f in dynamic_fields if f not in fixed_fields and f != "eventData"] + ["eventData"]
            if args.csv and neCSVwriter.fieldnames != new_fieldnames:
                neCSV.close()
                neCSV = open(args.csv, "w", newline='')
                neCSVwriter = csv.DictWriter(neCSV, fieldnames=new_fieldnames)
                neCSVwriter.writeheader()
                fieldnames = new_fieldnames

            eventCount += len(pageEvents)

            for event in pageEvents:
                if args.json:
                    neJSON.write(json.dumps(event) + "\n")
                if args.csv:
                    # Ensure all fields are present in the event dict, filling missing ones with None
                    event_with_defaults = {field: event.get(field, None) for field in fieldnames}
                    neCSVwriter.writerow(event_with_defaults)

                # Update last event time
                if 'occurredAt' in event:
                    event_time = dateutil.parser.isoparse(event['occurredAt'])
                    if last_event_time is None or event_time < last_event_time:
                        last_event_time = event_time

            if args.json: 
                neJSON.flush()
            if args.csv: 
                neCSV.flush()

            # Check if we should continue fetching (events are within one year)
            if last_event_time and last_event_time <= cutoff_time:
                print("Reached events older than one year, stopping")
                break

            # Update startAt for the next request
            if last_event_time:
                startAt = last_event_time.isoformat()
                log.debug("Updating endingBefore to: %s" % startAt)

    except KeyboardInterrupt:
        print("\nEvent download aborted")

    if args.json:
        neJSON.close()
    if args.csv:
        neCSV.close()

    if eventCount == 0:
        print("No events found in this network")
    else:
        print("Exported %s events" % eventCount)