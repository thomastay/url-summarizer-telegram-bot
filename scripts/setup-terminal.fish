#!/usr/bin/env fish

# Use jq to parse the JSON and extract name-value pairs
set name_value_pairs (gojq -r '.Values | to_entries | .[] | "\(.key)=\(.value)"' ./local.settings.json)

# Loop through the name-value pairs and export them as environment variables
for pair in $name_value_pairs
    set name (string split -m  1 '=' $pair | head -n  1)
    set value (string split -m  1 '=' $pair | tail -n  1)
    set -x $name $value
end
