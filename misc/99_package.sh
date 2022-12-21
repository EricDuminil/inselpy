#! /bin/sh

default_version="0.0.x"
version="${1:-$default_version}"

to_package="01_insel_example.py
02_test_insel.py
data
data/123.csv
data/123.dat
data/DEU_Stuttgart.107380_IWEC.epw
data/DEU_Stuttgart.107380_IWEC.txt
data/gengt_comparison.dat
templates
templates/a_times_b.insel
templates/a_times_b_iso8859.insel
templates/a_times_b_utf8.insel
templates/average_irradiance_on_tilted_surface.insel
templates/empty_if.insel
templates/expg.insel
templates/gengt_comparison.insel
templates/gengt_monthly_averages.insel
templates/get_irradiance_profile.insel
templates/i_sc.insel
templates/long_string.vseit
templates/merge_distinct_loops.insel
templates/mpp.insel
templates/nurnberg_v1.insel
templates/nurnberg_v2.insel
templates/odds_as_nans.insel
templates/one_to_ten.insel
templates/read_epw_file.insel
templates/read_relative_file.insel
templates/read_simple_file.insel
templates/remove_odds.insel
templates/short_string.vseit
templates/u_oc.insel
templates/write_params.insel
templates/x1_plus_x2.insel"

rm -f release/inselpy_"$version".zip
echo "$to_package" | zip -@ release/inselpy_"$version".zip
