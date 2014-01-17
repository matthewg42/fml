#!/bin/bash

tenmin=600
hour=3600
day=$(echo "$hour*24"  |bc)
week=$(echo "$day*7"   |bc)
month=$(echo "$day*30" |bc)
year=$(echo "$day*365" |bc)

renamers=""

main () {
    mk_temp_graph ten-minute $tenmin
    mk_temp_graph hour $hour
    mk_temp_graph day $day
    mk_temp_graph week $week
    mk_temp_graph month $month
    mk_temp_graph year $year

    renamers="$renamers /var/lib/fml/www/errors.png.png"
    rrdtool graph /var/lib/fml/www/errors.png.png -a PNG --title="Errors" \
                    -w 900 -h 60 \
                    --vertical-label "Count" \
                    'DEF:e1=/var/lib/fml/fml.rrd:crc_err:AVERAGE' \
                    'DEF:e2=/var/lib/fml/fml.rrd:no_reply:AVERAGE' \
                    'DEF:e3=/var/lib/fml/fml.rrd:other_err:AVERAGE' \
                    'LINE:e1#990000:Modbus CRC errors' \
                    'LINE:e2#990044:No reply' \
                    'LINE:e3#337700:Other errors'

    for f in $renamers; do
        mv $f ${f%.png}
    done
}

mk_temp_graph () {
    renamers="$renamers /var/lib/fml/www/temp_$1.png.png"
    rrdtool graph /var/lib/fml/www/temp_$1.png.png -a PNG --title="Temperature: $1" \
                -w 400 -h 100 \
                --start "N-$2" \
                --vertical-label "Deg C" \
                'DEF:t1=/var/lib/fml/fml.rrd:r240_0:AVERAGE' \
                'DEF:t2=/var/lib/fml/fml.rrd:r240_1:AVERAGE' \
                'DEF:t3=/var/lib/fml/fml.rrd:r240_4:AVERAGE' \
                'DEF:t6=/var/lib/fml/fml.rrd:r240_9:AVERAGE' \
                'LINE:t1#770000:Temp1' \
                'LINE:t2#007700:Temp2' \
                'LINE:t3#000077:Temp3' \
                'LINE:t6#000000:Temp6'
}

main "$@"
