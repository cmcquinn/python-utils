#!/usr/bin/env python3

"""diskimage.py: Create, partition, and format a disk image large enough to hold a rootfs created with multistrap, debootstrap, or similar tool."""

__author__      = "Cameron McQuinn"
__copyright__   = "Copyright 2019, Cameron McQuinn"
__email__       = "cameron.mcquinn@gmail.com"

import parted
import argparse
import subprocess

bootsize = 128 # size in Megabytes of boot partition
extraspace = 512 # amount of extra space in Megabytes to allocate for the rootfs partition

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='name of the disk image to create')
    parser.add_argument(
        '--path', help='path to folder containing rootfs to be copied into disk image', type=str, default='/tmp/multistrap')
    args = parser.parse_args()

    # determine size of rootfs folder
    result = subprocess.run('du --null -sm {}'.format(args.path).split(),
                            check=True, stdout=subprocess.PIPE, encoding='UTF-8')
    rootsize = int(result.stdout.split()[0]) # numeric size is at the beginning of the output line
    print('Found rootfs folder at {} with size {} MB'.format(args.path, rootsize))

    # create disk image file
    print('Creating empty disk image file...')
    imgpath = '/tmp/' + args.name
    image = open(imgpath, 'w')
    size = rootsize + bootsize + extraspace
    image.seek((size * 10**6) - 1)  # subtract one to align to 512-byte sector
    image.write('a')
    image.close()

    # setup loop device
    print('Setting up loopback device...')
    result = subprocess.run(
        'losetup -f --show {}'.format(imgpath).split(), check=True, stdout=subprocess.PIPE, encoding='UTF-8')
    devpath = result.stdout.strip()  # output from losetup gives path to loopback device
    print("loopback device created at {}".format(devpath))

    # partition disk image
    print('Partitioning disk image...')
    # create boot partition
    print('Creating boot partition...')
    device = parted.getDevice(devpath)
    disk = parted.freshDisk(device, 'gpt')
    bootPartSize = bootsize * 10 ** 6  # boot partiton is 128MB
    # convert from bytes to sectors
    bootlen = int(bootPartSize / device.sectorSize)
    bootgeom = parted.Geometry(device=device, start=1, length=bootlen)
    bootfs = parted.FileSystem(type='fat32', geometry=bootgeom)
    bootpart = parted.Partition(
        disk=disk, type=parted.PARTITION_NORMAL, fs=bootfs, geometry=bootgeom)
    bootpart.name = 'boot'
    disk.addPartition(partition=bootpart,
                    constraint=device.optimalAlignedConstraint)
    disk.commit()

    # create root partition
    print('Creating root partition')
    rootgeom = disk.getFreeSpaceRegions()[-1]
    rootfs = parted.FileSystem(type='ext4', geometry=rootgeom)
    rootpart = parted.Partition(
        disk=disk, type=parted.PARTITION_NORMAL, fs=rootfs, geometry=rootgeom)
    rootpart.name = 'Debian'
    disk.addPartition(partition=rootpart,
                    constraint=device.optimalAlignedConstraint)
    disk.commit()

    # delete loop device and recreate with partitions
    print('Removing loopback device and recreating with partition support...')
    result = subprocess.run('losetup -d {}'.format(devpath).split())
    result = subprocess.run(
        'losetup -f --show -P {}'.format(imgpath).split(), check=True, stdout=subprocess.PIPE, encoding='UTF-8')
    devpath = result.stdout.strip()  # output from losetup gives path to loopback device
    print("loopback device created at {}".format(devpath))

    # format partitions
    print('Formatting partitions...')
    subprocess.run('mkfs.fat -F 32 {}p1'.format(devpath).split(),
                check=True)  # format first partition to FAT32
    subprocess.run('mkfs.ext4 {}p2'.format(devpath).split(),
                check=True)  # format second parition to ext4

    # mount filesystems and copy files

    # delete loop device
    print('Cleaning up loopback device...')
    result = subprocess.run('losetup -d {}'.format(devpath).split())

if __name__ == "__main__":
    main()