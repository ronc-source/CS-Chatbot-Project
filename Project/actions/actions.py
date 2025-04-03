# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from amadeus import Client, ResponseError

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet

import dateparser
from datetime import datetime

import json

###############
# API CONSTANTS
###############

# Email rchar005@uottawa.ca for these credentials
CLIENT_ID = ""
CLIENT_SECRET = ""
AMADEUS = Client(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

#########
# CLASSES
#########

class ActionFindFlight(Action):

    def name(self) -> Text:
        return "action_find_flight"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        departure = tracker.get_slot("departure")
        departureTime = tracker.get_slot("departureTime")
        arrival = tracker.get_slot("arrival")
        arrivalTime = tracker.get_slot("arrivalTime")
        airline = tracker.get_slot("airline")
        preference = tracker.get_slot("preference")

        if departureTime:
            departureTime = formatTime(departureTime)

        if arrivalTime:
            arrivalTime = formatTime(arrivalTime)


        # Synthetic data handling for Boston to Denver due to Amadeus Flight API Maintenance
        # Assume we searched the API for BOS to DEN and this is the result returned
        flightAPIOfferList = testFlightData['data']

        # Collect all results that match the entities specified
        flightScheduleResults = []

        for flightOffer in flightAPIOfferList:

            departureInfo = flightOffer["itineraries"][0]["segments"][0]["departure"]
            arrivalInfo = flightOffer["itineraries"][0]["segments"][0]["arrival"]
            departureTimeInfo = flightOffer["itineraries"][0]["segments"][0]["departure"]["at"]
            arrivalTimeInfo = flightOffer["itineraries"][0]["segments"][0]["arrival"]["at"]
            airlineInfo = flightOffer["itineraries"][0]["segments"][0]["carrierCode"]

            # If the user asks for a departure time in HH:MM:SS
            if departureTime:
                departureTimeFound = departureTimeInfo.split('T')[1]

                # Split into [HH, MM, SS]
                departureTimeCheck = departureTime.split(":")
                departureTimeFoundCheck = departureTimeFound.split(":")

                # Check hours
                if int(departureTimeCheck[0]) > int(departureTimeFoundCheck[0]):
                    continue
                else:
                    if int(departureTimeCheck[0]) == int(departureTimeFoundCheck[0]):
                        if int(departureTimeCheck[1]) > int(departureTimeFoundCheck[1]):
                            continue
                        else:
                            if int(departureTimeCheck[1]) == int(departureTimeFoundCheck[1]):
                                if int(departureTimeCheck[2]) > int(departureTimeFoundCheck[2]):
                                    continue
            
            if arrivalTime:
                arrivalTimeFound = arrivalTimeInfo.split('T')[1]

                # Split into [HH, MM, SS]
                arrivalTimeCheck = arrivalTime.split(":")
                arrivalTimeFoundCheck = arrivalTimeFound.split(":")

                # Check hours
                if int(arrivalTimeCheck[0]) < int(arrivalTimeFoundCheck[0]):
                    continue
                else:
                    if int(arrivalTimeCheck[0]) == int(arrivalTimeFoundCheck[0]):
                        if int(arrivalTimeCheck[1]) < int(arrivalTimeFoundCheck[1]):
                            continue
                        else:
                            if int(arrivalTimeCheck[1]) == int(arrivalTimeFoundCheck[1]):
                                if int(arrivalTimeCheck[2]) < int(arrivalTimeFoundCheck[2]):
                                    continue
            
            # Airline slot is filled
            if airline and airline != airlineInfo:
                continue

            # Nonstop Preference check
            if preference == "nonstop":
                if not(flightOffer["oneWay"]):
                    continue
            
            flightScheduleResults.append(flightOffer)
        
        # Preference slot filled check
        if preference == "cheap" or preference == "cheapest" or preference == "least expensive":
            flightScheduleResults.sort(key=lambda flightFound: float(flightFound['price']['total']))
            cheapestFlight = flightScheduleResults[0]

            flightScheduleResults = [cheapestFlight]
        elif preference == "earliest":
            flightScheduleResults.sort(key=lambda flightFound: flightFound["itineraries"][0]["segments"][0]["departure"]["at"])
            earliestFlight = flightScheduleResults[0]

            flightScheduleResults = [earliestFlight]
        else:
            if preference == "shortest":
                flightScheduleResults.sort(key=lambda flightFound: flightFound["itineraries"][0]["duration"])
                shortestFlight = flightScheduleResults[0]

                flightScheduleResults = [shortestFlight]


        # Iterate through results found and show it to the user
        for flight in flightScheduleResults:
            departureInfo = flight["itineraries"][0]["segments"][0]["departure"]
            arrivalInfo = flight["itineraries"][0]["segments"][0]["arrival"]
            departureTimeInfo = flight["itineraries"][0]["segments"][0]["departure"]["at"]
            arrivalTimeInfo = flight["itineraries"][0]["segments"][0]["arrival"]["at"]
            airlineInfo = flight["itineraries"][0]["segments"][0]["carrierCode"]
            priceInfo = flight["price"]["total"]
            currency = flight["price"]["currency"]

            # List flight to user
            dispatcher.utter_message(
                text=f"Flight from {departureInfo['iataCode']} airport to {arrivalInfo['iataCode']} airport."
                     f"\nDeparture at {departureTimeInfo} from Terminal {departureInfo['terminal']}."
                     f"\nArrival at {arrivalTimeInfo} from Terminal {arrivalInfo['terminal']}."
                     f"\nFlight will be flown by {airlineInfo} airlines."
                     f"\nTotal cost of this trip is: {priceInfo} {currency}."
            )
        
        if len(flightScheduleResults) == 0:
            dispatcher.utter_message("Sorry we could not find any matching flight schedules.")

        return []


# Update departure after form is completed
class ActionUpdateDeparture(Action):
    def name(self):
        return "action_updateDeparture"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        newDepartureFound = next(tracker.get_latest_entity_values("departure"), None)

        if newDepartureFound:
            dispatcher.utter_message(text=f"Departure is now updated to {newDepartureFound}.")
            return [SlotSet("departure", newDepartureFound)]
        else:
            dispatcher.utter_message(text=f"Error: departure not specified.")
            return []


# Update arrival after form is completed
class ActionUpdateArrival(Action):
    def name(self):
        return "action_updateArrival"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        newArrivalFound = next(tracker.get_latest_entity_values("arrival"), None)

        if newArrivalFound:
            dispatcher.utter_message(text=f"Arrival is now updated to {newArrivalFound}.")
            return [SlotSet("arrival", newArrivalFound)]
        else:
            dispatcher.utter_message(text=f"Error: arrival not specified.")
            return []


# Validate the findFlight form
class ValidateFindFlightForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_findFlightForm"
    
    # Validate the departure slot
    def validate_departure(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:

        # If the departure location provided has an airport
        if validateLocation(slot_value):
            return {"departure": slot_value}
        else:
            dispatcher.utter_message(text="The departure location provided does not have an airport, please check your spelling.")
            return {"departure": None}

    def validate_arrival(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> Dict[Text, Any]:
        
        # If the arrival location provided has an airport
        if validateLocation(slot_value):
            return {"arrival": slot_value}
        else:
            dispatcher.utter_message(text="The arrival location provided does not have an airport, please check your spelling.")
            return {"arrival": None}
    

###########
# FUNCTIONS
###########

# Validate departure and arrival locations have an airport when provided a city
# Validation done through Amadeus API
def validateLocation(city):
    # NOTE:
    # Amadeus flight API call turned off due to maintenance on their end
    return True
    
    '''
    try:
        response = AMADEUS.reference_data.locations.get(
            keyword = city,
            subType = "AIRPORT"
        )

        if response.data and len(response.data[0].get('iataCode')) > 0:
            return True
        return False
    
    except ResponseError as error:
        print("The following error has occurred", error)
        return False'
    '''

# Calls the Amadeus API to get a list of real-time flight schedules and conver to JSON
# NOTE:
# Function turned off due to issue with Amadeus API under maintenance
# See synthetic data implementation at end of document for replacement result
'''
def getAPIFlightSchedules(departureAirport, arrivalAirport, departureDate):
    try:
        response = AMADEUS.shopping.flight_offers_search.get(
            originLocationCode = departureAirport,
            destinationLocationCode = arrivalAirport,
            departureDate = departureDate,
            adults='1', # fixed value as we do not support searching tickets for more than 1 person at the moment
            max=3 # return up to 3 flight offers to work with
        )

        return json.loads(json.dumps(response.data))
    
    except ResponseError as error:
        print("Error:", error)
        return None
'''

# Format time to 24 hour clock standard HH:MM:SS
def formatTime(time):
    # Use date parser
    time = dateparser.parse(time)
    if time:
        return time.strftime("%H:%M:%S")
    
    return None

# Format date to YYYY:MM:DD
def formatDate(date):
    # use date parser
    settings = {
        'PREFER_DATES_FROM': 'future'
    }
    date = dateparser.parse(date, settings=settings)
    if date:
        return date.date()
    return None


################
# SYNTHETIC DATA
################

# Example taken from https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search/api-reference
# Modified for the example: Boston to Denver

testFlightData = {
  "meta": {
    "count": 2,
    "links": {
      "self": "https://test.api.amadeus.com/v2/shopping/flight-offers?originLocationCode=SYD&destinationLocationCode=BKK&departureDate=2021-11-01&adults=1&max=2"
    }
  },
  "data": [
    {
      "type": "flight-offer",
      "id": "1",
      "source": "GDS",
      "instantTicketingRequired": False,
      "nonHomogeneous": False,
      "oneWay": False,
      "lastTicketingDate": "2021-11-01",
      "numberOfBookableSeats": 9,
      "itineraries": [
        {
          "duration": "PT14H15M",
          "segments": [
            {
              "departure": {
                "iataCode": "BOS",
                "terminal": "1",
                "at": "2025-04-02T11:35:00"
              },
              "arrival": {
                "iataCode": "DEN",
                "terminal": "2",
                "at": "2025-04-02T16:50:00"
              },
              "carrierCode": "united",
              "number": "212",
              "aircraft": {
                "code": "333"
              },
              "operating": {
                "carrierCode": "united"
              },
              "duration": "PT8H15M",
              "id": "1",
              "numberOfStops": 0,
              "blacklistedInEU": False
            },
            {
              "departure": {
                "iataCode": "MNL",
                "terminal": "1",
                "at": "2021-11-01T19:20:00"
              },
              "arrival": {
                "iataCode": "BKK",
                "at": "2021-11-01T21:50:00"
              },
              "carrierCode": "PR",
              "number": "732",
              "aircraft": {
                "code": "320"
              },
              "operating": {
                "carrierCode": "PR"
              },
              "duration": "PT3H30M",
              "id": "2",
              "numberOfStops": 0,
              "blacklistedInEU": False
            }
          ]
        }
      ],
      "price": {
        "currency": "CAD",
        "total": "355.34",
        "base": "255.00",
        "fees": [
          {
            "amount": "0.00",
            "type": "SUPPLIER"
          },
          {
            "amount": "0.00",
            "type": "TICKETING"
          }
        ],
        "grandTotal": "355.34"
      },
      "pricingOptions": {
        "fareType": [
          "PUBLISHED"
        ],
        "includedCheckedBagsOnly": True
      },
      "validatingAirlineCodes": [
        "PR"
      ],
      "travelerPricings": [
        {
          "travelerId": "1",
          "fareOption": "STANDARD",
          "travelerType": "ADULT",
          "price": {
            "currency": "EUR",
            "total": "355.34",
            "base": "255.00"
          },
          "fareDetailsBySegment": [
            {
              "segmentId": "1",
              "cabin": "ECONOMY",
              "fareBasis": "EOBAU",
              "class": "E",
              "includedCheckedBags": {
                "weight": 25,
                "weightUnit": "KG"
              }
            },
            {
              "segmentId": "2",
              "cabin": "ECONOMY",
              "fareBasis": "EOBAU",
              "class": "E",
              "includedCheckedBags": {
                "weight": 25,
                "weightUnit": "KG"
              }
            }
          ]
        }
      ]
    },
    {
      "type": "flight-offer",
      "id": "2",
      "source": "GDS",
      "instantTicketingRequired": False,
      "nonHomogeneous": False,
      "oneWay": True, # for synthetic data testing purposes set to True
      "lastTicketingDate": "2021-11-01",
      "numberOfBookableSeats": 9,
      "itineraries": [
        {
          "duration": "PT16H35M",
          "segments": [
            {
              "departure": {
                "iataCode": "BOS",
                "terminal": "1",
                "at": "2025-04-02T16:35:00"
              },
              "arrival": {
                "iataCode": "DEN",
                "terminal": "2",
                "at": "2025-04-02T20:50:00"
              },
              "carrierCode": "delta",
              "number": "212",
              "aircraft": {
                "code": "333"
              },
              "operating": {
                "carrierCode": "delta"
              },
              "duration": "PT8H15M",
              "id": "3",
              "numberOfStops": 0,
              "blacklistedInEU": False
            },
            {
              "departure": {
                "iataCode": "MNL",
                "terminal": "1",
                "at": "2021-11-01T21:40:00"
              },
              "arrival": {
                "iataCode": "BKK",
                "at": "2021-11-02T00:10:00"
              },
              "carrierCode": "PR",
              "number": "740",
              "aircraft": {
                "code": "321"
              },
              "operating": {
                "carrierCode": "PR"
              },
              "duration": "PT3H30M",
              "id": "4",
              "numberOfStops": 0,
              "blacklistedInEU": False
            }
          ]
        }
      ],
      "price": {
        "currency": "CAD",
        "total": "416.55",
        "base": "255.00",
        "fees": [
          {
            "amount": "0.00",
            "type": "SUPPLIER"
          },
          {
            "amount": "0.00",
            "type": "TICKETING"
          }
        ],
        "grandTotal": "355.34"
      },
      "pricingOptions": {
        "fareType": [
          "PUBLISHED"
        ],
        "includedCheckedBagsOnly": True
      },
      "validatingAirlineCodes": [
        "PR"
      ],
      "travelerPricings": [
        {
          "travelerId": "1",
          "fareOption": "STANDARD",
          "travelerType": "ADULT",
          "price": {
            "currency": "EUR",
            "total": "355.34",
            "base": "255.00"
          },
          "fareDetailsBySegment": [
            {
              "segmentId": "3",
              "cabin": "ECONOMY",
              "fareBasis": "EOBAU",
              "class": "E",
              "includedCheckedBags": {
                "weight": 25,
                "weightUnit": "KG"
              }
            },
            {
              "segmentId": "4",
              "cabin": "ECONOMY",
              "fareBasis": "EOBAU",
              "class": "E",
              "includedCheckedBags": {
                "weight": 25,
                "weightUnit": "KG"
              }
            }
          ]
        }
      ]
    }
  ],
  "dictionaries": {
    "locations": {
      "BKK": {
        "cityCode": "BKK",
        "countryCode": "TH"
      },
      "MNL": {
        "cityCode": "MNL",
        "countryCode": "PH"
      },
      "SYD": {
        "cityCode": "SYD",
        "countryCode": "AU"
      }
    },
    "aircraft": {
      "320": "AIRBUS A320",
      "321": "AIRBUS A321",
      "333": "AIRBUS A330-300"
    },
    "currencies": {
      "EUR": "EURO"
    },
    "carriers": {
      "PR": "PHILIPPINE AIRLINES"
    }
  }
}

# Convert to JSON for easier processing
testFlightData = json.loads(json.dumps(testFlightData))


# Trained Departure Cities
# 	- Boston
# 	- Columbus
# 	- Philadelphia
# 	- San Diego
# 	- New York
# 	- St. louis
# 	- Houston
# 	- Charlotte


# Trained Arrival Cities
# 	- Denver
# 	- Minneapolis
# 	- BWI
# 	- Pittsburgh
# 	- Newark
# 	- San Francisco
# 	- Los Angeles
# 	- Washington
# 	- Baltimore
# 	- Milwaukee
# 	- Miami
# 	- Burbank
# 	- Cleveland
# 	- Atlanta
#   - Dallas