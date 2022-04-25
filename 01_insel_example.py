import insel

print((insel.block('pi')))
print((insel.block('sum', 2, 3)))
print((insel.block('do', parameters=[1, 10, 1])))
print((insel.block('mtm', 12, parameters=['Strasbourg'])))

print((insel.template('a_times_b', a=7, b=3)))
print((insel.template('photovoltaic/i_sc',
      pv_id='008823', temperature=25, irradiance=1000)))
print((insel.template('x1_plus_x2', x=[4, 5])))

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
