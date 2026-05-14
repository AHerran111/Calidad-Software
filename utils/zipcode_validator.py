from geopy.geocoders import Nominatim


def validar_zip(zipcode):

    geolocator = Nominatim(user_agent="cs2026_zip")

    location = geolocator.geocode(zipcode, country_codes="mx")

    address = str(location).split(",")

    # print(address)
    if address == None:
        raise Exception

    return address[1], address[3]
