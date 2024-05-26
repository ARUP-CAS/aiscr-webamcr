#!/bin/bash

generate_random_string() {
    local length=$1
    tr -dc A-Za-z0-9 </dev/urandom | head -c $length
}

# Generate two random strings of length 10
STRING1=$(generate_random_string 10)
STRING2=$(generate_random_string 10)
REDIS_PASSWORD=$(cat /run/secrets/redis_pass)

# Run the Django management command with the generated strings as arguments
python3 manage.py write_value_to_redis "$STRING1" "$STRING2"

read_value_from_redis() {
    local key=$1
    redis-cli -h redis -a "$REDIS_PASSWORD" GET "$key"
}

delete_value_from_redis() {
    local key=$1
    # Connect to the Redis server running in Docker with hostname 'redis' and use the password
    redis-cli -h redis -a "$REDIS_PASSWORD" DEL "$key"
}

# Try to read the value from Redis and compare with STRING2
for i in {1..60}; do
    VALUE_FROM_REDIS=$(read_value_from_redis "$STRING1")

    if [ "$VALUE_FROM_REDIS" == "$STRING2" ]; then
        echo "The value from Redis matches STRING2."
        delete_value_from_redis "$STRING1"
        exit 0
    else
        echo "Attempt $i: The value from Redis does not match STRING2. Retrieved value: $VALUE_FROM_REDIS"
    fi

    # Wait for 1 second before the next attempt
    sleep 1
done

# If the loop completes, the values do not match
echo "The value from Redis did not match STRING2 after 60 attempts."
delete_value_from_redis "$STRING1"
exit 1
