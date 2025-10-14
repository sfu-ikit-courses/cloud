#!/bin/sh

PORT=${PORT:-8080}
LOG="req.log"

echo "Server listening on port $PORT"

while true; do

    printf "HTTP/1.1 200 OK\r\n\r\n%s\r\n" "$(ls -l)" | nc -l -p "$PORT" | while IFS= read -r line; do

        echo "$line" >> "$LOG"

        if echo "$line" | grep -q '^GET'; then
            
            path=$(echo "$line" | awk '{print $2}')
            query=$(echo "$path" | cut -d'?' -f2)

            file=$(echo "$query" | grep -o 'file=[^&]*' | cut -d'=' -f2)
            mode=$(echo "$query" | grep -o 'mode=[^&]*' | cut -d'=' -f2)

            case "$file" in
                *"/"*|*..*) file="";;
            esac

            echo "$mode" | grep -Eq '^[0-7]{3,4}$' || mode=""

            if [ -n "$file" ] && [ -n "$mode" ] && [ -e "./$file" ]; then
                chmod "$mode" "./$file"
                res="OK Changed $file -> $mode"
            else
                res="OK" 
            fi

            echo $res

            break  
        fi
    done
done
