import requests
import json
import xlsxwriter
import dateutil.parser
from datetime import datetime, timedelta
from dateutil import tz
import argparse
import os

server = 'https://cloud.sensolus.com'
reportName = 'journeys'

BRUSSELS_TZ = tz.gettz('Europe/Brussels')


def getSerials(apiKey:str):
    devicesUrl = server + '/rest/api/v2/devices?apiKey=' + apiKey
    r = requests.get(devicesUrl)

    d = r.json()
    return list(map(lambda a: a['serial'], d))


def addJourneys(apiKey: str, worksheet: xlsxwriter.worksheet, dateformat, serial: str, startRow: int):
    yesterday = datetime.now(BRUSSELS_TZ) - timedelta(days=1)
    start = datetime(yesterday.year, yesterday.month,
                     yesterday.day, 0, 0, 0, tzinfo=BRUSSELS_TZ)
    end = datetime(yesterday.year, yesterday.month,
                   yesterday.day, 23, 59, 59, tzinfo=BRUSSELS_TZ)

    q = {'from': start.isoformat(), 'to': end.isoformat(), 'apiKey': apiKey}

    journeyUrl = server + '/rest/api/v2/sigfoxdevices/' + serial + '/journey'
    r = requests.get(journeyUrl,  params=q)

    journey = r.json()

    # check if we have something
    if not 'journeyParts' in journey:
        return

    # let's only focus on the trips ...
    trips = list(filter(lambda e: e['type'] ==
                        'ON_THE_MOVE', journey['journeyParts']))

    print(f"Trip length {len(trips)}")

    row = startRow

    for t in trips:
        start = dateutil.parser.isoparse(
            t['startLocation']['timestamp']).astimezone(tz=BRUSSELS_TZ)
        stop = dateutil.parser.isoparse(
            t['stopLocation']['timestamp']).astimezone(tz=BRUSSELS_TZ)

        worksheet.write(row, 0, serial)
        worksheet.write(row, 1, t['startLocation'].get('address'))
        worksheet.write_number(row, 2, t['startLocation']['lat'])
        worksheet.write_number(row, 3, t['startLocation']['lng'])
        worksheet.write_datetime(row, 4, start.replace(tzinfo=None), dateformat)
        worksheet.write(row, 5, t['stopLocation'].get('address'))
        worksheet.write_number(row, 6, t['stopLocation']['lat'])
        worksheet.write_number(row, 7, t['stopLocation']['lng'])
        worksheet.write_datetime(row, 8, stop.replace(tzinfo=None), dateformat)
        worksheet.write_number(row, 9, round(t.get('distance') / 1000,3))
        worksheet.write_number(row, 10, round((stop-start).total_seconds() / 60,0))
        row = row + 1

    return row


def lambda_handler(event, context):
    if os.environ.get('key'):
        apiKey = os.environ.get('key')
    
    print(apiKey)


    # write to XLS
    filename = '/tmp/journey.xlsx'

    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet('data')

    dateformat = workbook.add_format({'num_format': 'dd/mm/yyyy HH:mm:ss'})

    serials = getSerials(apiKey)

    rows = 1
    for serial in serials:
        print(f"Handling {serial}")
        rows = addJourneys(apiKey, worksheet, dateformat, serial, rows)

    columns = [{'header': 'Serial'},
               {'header': 'Start address'},
               {'header': 'Start latitude'},
               {'header': 'Start longitude'},
               {'header': 'Start time'},
               {'header': 'Stop address'},
               {'header': 'Stop latitude'},
               {'header': 'Stop longitude'},
               {'header': 'Stop time'},
               {'header': 'Distance (km)'},
               {'header': 'Trip duration (minutes)'},
               ]
    worksheet.add_table(
        0, 0, rows-1, 10, {'banded_rows': True, 'name': 'Journeys', 'columns': columns, 'first_column': True})

    # change width for some columns
    for i in [0,2,3,6,7,9]:
        worksheet.set_column(i, i, 15) 
    for i in [4,8,9]:
        worksheet.set_column(i, i, 25) 
    for i in [1,5]:
        worksheet.set_column(i, i, 40) 
    

    workbook.close()

    # upload the workbook
    files = {'file': open(filename, 'rb')}
    r = requests.post(server + '/rest/api/v2/reports/custom?apiKey=' +
                      apiKey + '&reportName=' + reportName, files=files)
    print(r.status_code)
    print(r.text)

    return {
        'rows': rows
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get dev key')
    parser.add_argument('key', 
                    help='API key')
    args = parser.parse_args()          
    
    apiKey = args.key

    lambda_handler(None, None)
