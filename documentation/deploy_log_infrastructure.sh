#!/bin/sh
# GET USER ID
_user=${1}
if [ ${_user} = ""]; then
  echo "ERROR - YOU DID NOT PROVIDE THE USER ARGUMENT. EXITING"
  echo "FAILURE!"
  exit 0
fi

_user_id=$(id -u ${1})
if [ $? -eq 0 ]; then
  echo "INFO - WORKING WITH USER ${1} and ID ${_user_id}"
else
  echo "ERROR - COULD NOT GET USER ${1} ID. EXITING"
  echo "FAILURE!"
  exit 0
fi

# VERIFY .creds FILE PREREQUISITE
if [ -f "/home/${_user}/.creds" ]; then
  echo "INFO - /home/${_user}/.creds exists"
else
  echo "ERROR - /home/${_user}/.creds is missing. Please create the file"
  echo "FAILURE!"
  exit 0
fi



# GET LATEST PACKAGES LIST
apt-get update
if [ $? -eq 0 ]; then
  echo "OK - updated apt-get data"
else
  echo "ERROR - failed to update apt-get data"
fi

# INSTALL CIFS-UTILS
apt-get install cifs-utils -y
if [ $? -eq 0 ]; then
  echo "OK - installed cifs-utils"
else
  echo "ERROR - failed to install cifs-utils via apt-get. EXITING"
  echo "FAILURE!"
  exit 0
fi

# CREATE DIRECTORY TO MOUNT TO
if [ -d "/mnt/AIRTELLOGSDIR" ]; then
  echo "INFO - /mnt/AIRTELLOGSDIR exists"
else
  mkdir /mnt/AIRTELLOGSDIR
  if [ $? -eq 0 ]; then
    echo "OK - /mnt/AIRTELLOGSDIR was created now"
  else
    echo "ERROR - /mnt/AIRTELLOGSDIR could not be created. EXITING"
    echo "FAILURE!"
    exit 0
  fi
fi

# CREATE BACKUP FOR FSTAB
cp /etc/fstab /home/${_user}/fstab
if [ $? -eq 0 ]; then
  echo "OK - BACKUP created for /etc/fstab in /home/${_user}/fstab"
else
  echo "ERROR - BACKUP for /etc/fstab could not be created. EXITING"
  echo "FAILURE!"
  exit 0
fi

# ADD MOUNT LINE IN FSTAB IF NEEDED
if grep -q "//172.16.86.199/airtellogs" /etc/fstab; then
  echo "INFO - AIRTELLOGS is already in /etc/fstab"
  umount /mnt/AIRTELLOGSDIR
  if [ $? -eq 0 ]; then
    echo "OK - Unmounted /mnt/AIRTELLOGSDIR"
  else
    echo "WARNING - Failed to Unmount /mnt/AIRTELLOGSDIR. Maybe there is nothing to Unmount"
  fi
else
  echo "//172.16.86.199/airtellogs /mnt/AIRTELLOGSDIR cifs credentials=/home/${_user}/.creds,uid=${_user_id},file_mode=0777,dir_mode=0777,noperm 0 0" >> /etc/fstab
  if [ $? -eq 0 ]; then
    echo "OK - AIRTELLOGS SHARE was added to /etc/fstab"
  else
    echo "ERROR - /mnt/AIRTELLOGSDIR could not be added to /etc/fstab"
    echo "INFO - Applying backup FSTAB to /etc/fstab"
    cp /home/${_user}/fstab /etc/fstab
    if [ $? -eq 0 ]; then
      echo "OK - BACKUP applied to /etc/fstab from /home/${_user}/fstab. EXITING"
    else
      echo "ERROR - BACKUP for /etc/fstab could NOT be APPLIED. EXITING"
    fi

    echo "FAILURE!"
    exit 0
  fi
fi

# MOUNT
mount -a
if [ $? -eq 0 ]; then
  echo "OK - ALL drives were mounted"
  echo "SUCCESS!"
else
  echo "ERROR - MOUNT FAILED"
  echo "FAILURE!"
fi
