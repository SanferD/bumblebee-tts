#!/bin/bash

INPUT_DIR="$1"
OUTPUT_DIR="$2"

echo "input-dir=${INPUT_DIR}"
echo "output-dir=${OUTPUT_DIR}"
read -p "Do you wish to continue? " -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]
then
    exit 1
fi

mkdir -p $OUTPUT_DIR

# iterate over all the assumed wav files and convert to flat list of wav files with unique integer names
i=1
for filename in $(find $INPUT_DIR -type f); do
    extension="${filename##*.}"
    if [[ "$extension" == "wav" ]]; then
        echo mv $filename "$OUTPUT_DIR/$i.${extension}"
        #mv $filename "$OUTPUT_DIR/$i.${extension}"
        i=$((i + 1))
    fi
done

