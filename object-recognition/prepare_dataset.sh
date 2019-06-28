#!/bin/bash
#
#  create-structure.sh
#
# This script downloads the enire KSCGR dataset from 
# [Murase](http://www.murase.m.is.nagoya-u.ac.jp/KSCGR/download.html) site, 
# extracts the content and create the whole structure to be used for training 
# and testing neural networks.
# 

KSCGR_SITE=http://www.murase.m.is.nagoya-u.ac.jp/KSCGR/download/
TRAINSETS="1 2 3 4 5"
TESTSETS="10 11"
ACTIONS="boild-egg ham-egg kinshi-egg omelette scramble-egg"
ACTEST10=("ham-egg" "omelette" "scramble-egg" "boild-egg" "kinshi-egg")
ACTEST11=("omelette" "scramble-egg" "boild-egg" "kinshi-egg" "ham-egg")
SOURCE=`pwd`

if [ $# -ne 1 ]; then
    echo "ERROR: Usage:"
    echo "   ${0} <OUTPUT_FOLDER>"
    exit 1
fi
OUTPUT=$1

function download {
    echo "- Downloading ${KSCGR_SITE}data${1}.tar.gz to ${OUTPUT}"
    wget -v "${KSCGR_SITE}data${1}.tar.gz"
    echo "- Downloading ${KSCGR_SITE}label${1}.tar.gz to ${OUTPUT}"
    wget -v "${KSCGR_SITE}label${1}.tar.gz"
}

function extract_train {
    echo "- Decompressing data${1}.tar.gz"
    tar -zxf "data${1}.tar.gz" -C "data${1}"
    
    for action in ${ACTIONS}; do
        echo "    - ${action}-${1}.tar.gz"
        mkdir -p "data${1}/${action}"
        tar -zxf "data${1}/${action}-${1}.tar.gz" -C "data${1}/${action}/"
        mv "data${1}/${action}/compressed/image_jpg"/* "data${1}/${action}/"
        rm -rf "data${1}/${action}/compressed/"
    done
    echo "- Decompressing label${1}.tar.gz"
    tar -zxf "label${1}.tar.gz" -C "data${1}"
}

function extract_test {
    echo "- Decompressing data${1}.tar.gz"
    tar -zxf "data${1}.tar.gz" -C "data${2}"
    
    if [ $1 -eq 10 ]; then
        for id in ${TRAINSETS}; do
            new_id=$((${id} - 1))
            echo "    - test_data_0${id}.tar.gz"
            mkdir -p "data${2}/${ACTEST10[${new_id}]}"
            tar -zxf "data${2}/test_data_0${id}.tar.gz" -C "data${2}/${ACTEST10[${new_id}]}/"
            mv "data${2}/${ACTEST10[${new_id}]}/compressed/image_jpg"/* "data${2}/${ACTEST10[${new_id}]}/"
            rm -rf "data${2}/${ACTEST10[${new_id}]}/compressed/"
        done
    elif [ $1 -eq 11 ]; then
        for id in ${TRAINSETS}; do
            new_id=$((${id} - 1))
            echo "    - test_data_0${id}.tar.gz"
            mkdir -p "data${2}/${ACTEST11[${new_id}]}"
            tar -zxf "data${2}/test_data_0${id}.tar.gz" -C "data${2}/${ACTEST11[${new_id}]}/"
            mv "data${2}/${ACTEST11[${new_id}]}/compressed/image_jpg"/* "data${2}/${ACTEST11[${new_id}]}/"
            rm -rf "data${2}/${ACTEST11[${new_id}]}/compressed/"
        done
    fi
    echo "- Decompressing label${1}.tar.gz"
    tar -zxf "label${1}.tar.gz" -C "data${2}"
}

function rename_imgs {
    for action in ${ACTIONS}; do
        echo "    - Renaming RGB images from: data${1}/${action}/"
        idimg=0
        for name in `ls "data${1}/${action}/"`; do
            mv "data${1}/${action}/$name" "data${1}/${action}/${idimg}.jpg"
            idimg=$((${idimg} + 1))
        done
    done
}

function rename_labels_training {
    for action in ${ACTIONS}; do
        echo "- Renaming file data${1}/${action}-${1}.txt"
        mv "data${1}/${action}-${1}.txt" "data${1}/${action}.txt"
    done
}

function rename_labels_testing {
    if [ $1 -eq 10 ]; then
        for id in ${TRAINSETS}; do
            new_id=$((${id} - 1))
            echo "- Renaming file data${2}/data${1}_0${id}.txt to data${2}/${ACTEST10[${new_id}]}.txt"
            mv "data${2}/data${1}_0${id}.txt" "data${2}/${ACTEST10[${new_id}]}.txt"
        done
    elif [ $1 -eq 11 ]; then
        for id in ${TRAINSETS}; do
            new_id=$((${id} - 1))
            echo "- Renaming file data${2}/data${1}_0${id}.txt to data${2}/${ACTEST11[${new_id}]}.txt"
            mv "data${2}/data${1}_0${id}.txt" "data${2}/${ACTEST11[${new_id}]}.txt"
        done
    fi
}

function process_train {
    cd $OUTPUT
    for data in $TRAINSETS; do
        mkdir -p "data$data"

        # download dataset
        download $data

        # extract content
        extract_train $data

        # fix names images
        rename_imgs $data

        # fix names labels
        rename_labels_training $data
    done
}

function process_test {
    cd $OUTPUT
    for data in $TESTSETS; do
        index=$(( $data - 4 ))
        mkdir -p "data"${index}

        # download dataset
        download $data

        # extract content
        extract_test $data $index

        # fix names images
        rename_imgs $index

        # fix names labels
        rename_labels_testing $data $index
    done
}

process_train
process_test

cd ${SOURCE}
python prepare_dataset.py ${OUTPUT}

allpaths=""
ALLSETS="1 2 3 4 5 6 7"
for data in $ALLSETS; do
    for action in ${ACTIONS}; do
        allpaths="${allpaths} ${OUTPUT}/data${data}/${action}.txt"
    done
done
cat ${allpaths} > "${OUTPUT}/paths.txt"

#echo "- Reading ${OUTPUT}/paths.txt file"
#python resize.py "${OUTPUT}/paths.txt" 256

