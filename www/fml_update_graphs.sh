#!/bin/bash

tenmin=600
hour=3600
day=$(echo "$hour*24"  |bc)
week=$(echo "$day*7"   |bc)
month=$(echo "$day*30" |bc)
year=$(echo "$day*365" |bc)
slave_id=100

renamers=""

main () {
    mk_temp_graph ten-minute $tenmin
    #mk_temp_graph hour $hour
    #mk_temp_graph day $day
    mk_temp_graph week $week
    #mk_temp_graph month $month
    #mk_temp_graph year $year

    renamers="$renamers /var/lib/fml/www/errors.png.png"
    rrdtool graph /var/lib/fml/www/errors.png.png -a PNG --title="Errors" \
                    -w 900 -h 60 \
                    --vertical-label "Count" \
                    'DEF:e1=/var/lib/fml/fml.rrd:crc_err:AVERAGE' \
                    'DEF:e2=/var/lib/fml/fml.rrd:no_reply:AVERAGE' \
                    'DEF:e3=/var/lib/fml/fml.rrd:other_err:AVERAGE' \
                    'LINE:e1#990000:Modbus CRC errors' \
                    'LINE:e2#990044:No reply' \
                    'LINE:e3#337700:Other errors' > /dev/null 2>&1

    for f in $renamers; do
        mv $f ${f%.png}
    done
}

mk_temp_graph () {
    renamers="$renamers /var/lib/fml/www/temp_$1.png.png /var/lib/fml/www/voltage_$1.png.png /var/lib/fml/www/current_$1.png.png"
    rrdtool graph /var/lib/fml/www/temp_$1.png.png -a PNG --title="Temperature: $1" \
                -w 400 -h 100 \
                --start "N-$2" \
                --vertical-label "Deg C" \
                "DEF:t1=/var/lib/fml/fml.rrd:r${slave_id}_0:AVERAGE" \
                'LINE:t1#770000:Temp' > /dev/null 2>&1

    rrdtool graph /var/lib/fml/www/voltage_$1.png.png -a PNG --title="Voltage: $1" \
                -w 400 -h 100 \
                --start "N-$2" \
                --vertical-label "Volts" \
                "DEF:v1=/var/lib/fml/fml.rrd:r${slave_id}_1:AVERAGE" \
                "DEF:v2=/var/lib/fml/fml.rrd:r${slave_id}_2:AVERAGE" \
                'LINE:v1#009999:Voltage1' \
                'LINE:v2#00ee00:Voltage2' > /dev/null 2>&1

    rrdtool graph /var/lib/fml/www/current_$1.png.png -a PNG --title="Current: $1" \
                -w 400 -h 100 \
                --start "N-$2" \
                --vertical-label "Amps" \
                "DEF:c1=/var/lib/fml/fml.rrd:r${slave_id}_3:AVERAGE" \
                "DEF:c2=/var/lib/fml/fml.rrd:r${slave_id}_3:AVERAGE" \
                'LINE:c1#000077:Current1' \
                'LINE:c2#440077:Current2' > /dev/null 2>&1

}

main "$@"
