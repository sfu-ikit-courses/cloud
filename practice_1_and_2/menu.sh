#!/bin/sh

while true; do
    echo "Select an action:"
    echo "1 - Execute commands"
    echo "2 - Calculate expression (a op1 b op2 c)"
    echo "0 - Exit"

    read -p "> " choice

    case "$choice" in
        1)
            echo "Command execution mode (type 'exit' to leave)"
            while true; do
                read -p "> " cmd
                [ "$cmd" = "exit" ] && break
                sh -c "$cmd"
            done
            ;;
        2)
            echo "Enter expression in format: a op1 b op2 c"
            echo "Supported operators: + - * /"
            echo "Type 'exit' to return to main menu"

            while true; do
                read -p "expr> " a op1 b op2 c

                [ "$a" = "exit" ] && break

                if [ -z "$a" ] || [ -z "$op1" ] || [ -z "$b" ] \
                || [ -z "$op2" ] || [ -z "$c" ]; then
                    echo "Invalid input. Format: a op1 b op2 c"
                    continue
                fi

                res=$(echo "$a $op1 $b $op2 $c" | bc -l 2>/dev/null )

                if [ $? -ne 0 ]; then
                    echo "Error in calculation. Check your expression."
                else
                    echo "Result: $res"
                fi

            done
            ;;
        0)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac

done