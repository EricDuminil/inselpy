set macro
set style data lines
my_line_width = "1"
set linetype 1 linecolor rgbcolor "#000000" linewidth @my_line_width
set title "$manufacturer_name$ $name$ η(DC)"
set ylabel 'Efficiency [%]'
set ytics nomirror
set xtics nomirror
set xlabel 'Power [%]'

set yrange [80:100]
set xrange [0:100]

set terminal dumb $width||100$ $height||40$
set output '$plots_folder||plots$/inverter_eta_curve_$iv_id$.txt'

plot "$result_folder$/insel.gpl" using ($1*100):($2*100) title "Eta(DC)"
