from sattelite_report import generate_multisatellite_report
from weather import get_weather_info
from datetime import datetime

def generateReport(boundingBox, id):
    print(f"Generating report for bounding box: {boundingBox} and user ID: {id}")
    myfield=[[boundingBox[0], boundingBox[2]], [boundingBox[0], boundingBox[3]], [boundingBox[1],boundingBox[3]], [boundingBox[1],boundingBox[2]]]
    lat=(boundingBox[0]+boundingBox[1])/2
    lon=(boundingBox[2]+boundingBox[3])/2
    weatherReport=get_weather_info(lat,lon)
    cropHealth=generate_multisatellite_report(myfield, id ,str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))[0]
    # print("Weather Report:", weatherReport)
    # print("Crop Health Report:", cropHealth)
    print("report done")
    return f'''
The following is the weather report at the farmer's field

{weatherReport}

This is the crop health report given by the satellite

{cropHealth}
'''
