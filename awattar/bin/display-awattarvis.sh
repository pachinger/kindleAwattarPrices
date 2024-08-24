#!/bin/sh

# from https://github.com/x-magic/kindle-weather-stand-alone/blob/master/extensions/weather-stand/bin/start.sh

cd "$(dirname "$0")"

# Clean up display, show initialisation message
/usr/sbin/eips -c
/usr/sbin/eips -c
/usr/sbin/eips 1 10 'Awattar API visualizer'
/usr/sbin/eips 1 11 'url: http://192.168.1.90:5000/awattar.png'
/usr/sbin/eips 1 12 'Initialising...'
/usr/sbin/eips 1 13 'Stopping services'
# Shutdown as many services as possible
/etc/init.d/framework stop
/etc/init.d/powerd stop

while true
do
	current_datetime=$(date '+%Y-%m-%d %H:%M:%S')

	# Export the current date and time
	export CURRENT_DATETIME="$current_datetime"
	
	eips 1 14 'Current datetime:'
	eips 1 15 "$CURRENT_DATETIME"
	
	/usr/sbin/eips 1 16 'Enabling Wifi'
    # Enable WiFi
    /usr/bin/lipc-set-prop com.lab126.cmd wirelessEnable 1
    sleep 30
    
    # Update prices image
	/usr/sbin/eips 1 17 'deleting image'
    rm awattar.png

	if wget http://192.168.1.90:5000/awattar.png; then
		/usr/sbin/eips 1 18 'image response successful, refreshing'
		sleep 5
		eips -c
		eips -c
		eips -g awattar.png
	else
		/usr/sbin/eips 1 18 'fetching image failed, showing error image'
		/usr/sbin/eips 1 19 'trying again in 6 hours'
		sleep 20
		eips -c
		eips -c
		eips -g awattarKindleError.png
	fi
    
    # Disable WiFi, set wakeup alarm then back to sleep
    # Alarm is in seconds, so 3600 means it will wake it self up every hour
    /usr/bin/lipc-set-prop com.lab126.cmd wirelessEnable 0
    sleep 15
    echo "" > /sys/class/rtc/rtc1/wakealarm
    # Following line contains sleep time in seconds
    # Use +3600 (1hr) for Dark Sky API, and +10800 (3hrs) for OpenWeatherMap API
    echo "+21600" > /sys/class/rtc/rtc1/wakealarm
    # Following line will put device into deep sleep until the alarm above is triggered
    echo mem > /sys/power/state
done
