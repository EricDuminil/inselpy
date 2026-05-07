set macro
set style data lines
my_line_width = "1"
set linetype 1 linecolor rgbcolor "#000000" linewidth @my_line_width
set title "$name$ I(V)"
set ylabel 'Current [A]'
set ytics nomirror
set xtics nomirror
set xlabel 'Voltage [V]'
set yrange [ 0 : floor($i_max$)+1 ]
set xrange [ 0 : $u_max$ ]

set y2label 'Power [W]'
set y2range [0 : $p_max$]
set y2tics 50

set terminal dumb $tty_width||100$ $tty_height||40$
set output '$plots_folder||plots$/iv_curve_$pv_id$.txt'

plot "$result_folder$/insel.gpl" using 1:2 axis x1y1 title "I(V)",\
     "$result_folder$/insel.gpl" using 1:3 axis x1y2 title "P(V)"
