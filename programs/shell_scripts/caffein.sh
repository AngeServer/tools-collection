#/bin/bash

function caf() {
    PIDS=$(pgrep caffeinate)
    if [ -n "${PIDS}" ]; then 
        echo "# Already Caffeinated."
    else
        caffeinate -dims &
        echo "Caffeine Drank."
    fi
}

function decaf() {
    PIDS=$(pgrep caffeinate)
    if [ -n "${PIDS}" ]; then
        echo "kill -9 ${PIDS}"
        kill -9 ${PIDS}
        echo "Decaf."
    else
        echo "# No caffeine left."
    fi
}

if [ $# = 0 ]; then
    echo "caffein.sh [drink | decaf]"
    exit 1
elif [ $1 = "drink" ]; then
    caf
elif [ $1 = "decaf" ]; then
    decaf    
fi