#!/bin/bash
cd /home/happy/rknpu_build/drivers/rknpu
make -C /lib/modules/$(uname -r)/build M=$(pwd) modules_install
depmod -a
