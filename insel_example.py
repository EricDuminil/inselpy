import insel

print insel.block('pi')
print insel.block('sum', 2, 3)
print insel.block('do', parameters = [1,10,1])
print insel.block('mtm', 12, parameters = ['Strasbourg'])

print insel.template('a_times_b', a = 7, b = 3)
print insel.template('i_sc', pv_id = '008823', temperature= 25, irradiance = 1000, bp_folder = '/usr/local/INSEL/resources/data/bp/')
