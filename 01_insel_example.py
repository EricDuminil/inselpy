import insel


# NOTE: Templates will be searched inside the 'templates/' folder, relative to the current working directory.

name = 'Roma'
lat = 41.8
lon = 12.58
timezone = 1

irradiances = insel.template('weather/get_irradiance_profile', latitude=lat, longitude=lon)
print(irradiances)

print((insel.template('weather/average_irradiance_on_tilted_surface',
                      tilt=30,
                      azimuth=180,
                      irradiance_profile=irradiances,
                      latitude=lat,
                      longitude=lon,
                      timezone=timezone)))
