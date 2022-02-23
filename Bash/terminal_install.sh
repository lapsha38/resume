#!/bin/bash

img_path=/mnt/data/terminal_new.img.gz

# show disks
function get_disk_info {
        # user friendly iter
        iter=1
        # get disks list
        disks=$(lsblk -po NAME | grep -w sd. | grep -v iso)
        
        for item in ${disks[*]}
        do
                # get disk size
                get_size=$(lsblk $item -o SIZE | head -n 2 | tail -n 1)
                # show path + siza
                printf "%s" $iter ') ' $item ' Размер диска: ' $get_size
                
                iter=$(expr $iter + 1)
                printf "\n"
        done
        # call next func
        check_valid_disk
}

# check correct input
function check_valid_disk {
        # get disk count
        disks=$(lsblk | grep -w sd. | grep -v iso | wc -l)
        echo "Type disk number like: 1"
        read disk
        # if input is int => go next
        if [[ $disk =~ ^-?[0-9]+$ ]]; then
                # if input is 0 or str => show error
                if [ $disk -gt $disks ] || [ $disk = 0 ] ; then
                        echo "Error: disk number can not be null "$disks
                        check_valid_disk
                else
                        get_disk_number
                fi
        else
                # пользователь ввел неверные данные - пишем об этом и заново просим ввести цифру
                echo "Error: type integer only"
                check_valid_disk
        fi
}


function get_disk_number {
        # get disk number from path
        disk_path=$(lsblk -po NAME | grep -w sd. | grep -v iso | head -n $disk | tail -n 1)
        echo Choise: $disk_path
        echo -e "Install img to disk "$disk_path"? All info from "$disk_path" will be destroyed!\nType y"
        read answer
        if [[ "$answer" != "${answer#[Yy]}" ]] ;then
                start_dd
        else
                echo "Error: input is not y, start again"
                get_disk_info
        fi
}

function start_dd {
        # check file extension (.img or .gz)
        extension="${img_path##*.}"
        # use gunzip
        if [[ $extension == "gz" ]]; then
                gunzip -c $img_path | dd of=$disk_path status=progress
        fi
        # use img with dd
        if [[ $extension == "img" ]]; then
                dd if=$img_path of=$disk_path status=progress
        fi

        echo -e "\nThe image has been successfully installed, remove the flash drive and restart the terminal"

}
# main func
get_disk_info
