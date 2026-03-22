set terminal dumb 100, 40
set output '$plot_folder$/sorted_sine_and_cos.txt'

plot "$result_folder$/insel.gpl" title "Sorted sine",\
     "$result_folder$/insel2.gpl" title "Cosine"
