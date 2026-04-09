#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

if [ "$#" -ne 1 ]; then
    echo "Sintaxis: $0 MASTER_HOSTNAME"
    exit -1
fi

MASTER_HOSTNAME=$1
CURRENT_HOST=$(hostname)

sed -i '/127.0.1.1.*packer-/d' /etc/hosts 2>/dev/null
sed -i '/127.0.2.1/d' /etc/hosts 2>/dev/null

if [ -b /dev/sdb ]; then
    DISK0=/dev/sdb
elif [ -b /dev/vdb ]; then
    DISK0=/dev/vdb
fi

if [ -b /dev/sdc ]; then
    DISK1=/dev/sdc
elif [ -b /dev/vdc ]; then
    DISK1=/dev/vdc
fi

if [ -b /dev/sdd ]; then
    DISK2=/dev/sdd
elif [ -b /dev/vdd ]; then
    DISK2=/dev/vdd
fi

# Format and mount disks to be used with Hadoop HDFS and Spark
if [ ! -d "/data/disk0" ]; then
    mkdir -p /data/disk0 >& /dev/null
    mkfs.ext4 -F $DISK0
    mount $DISK0 /data/disk0
    chmod 1777 /data/disk0
else
    if ! grep -Fq $DISK0 /proc/mounts ; then
	mount $DISK0 /data/disk0 >& /dev/null
	chmod 1777 /data/disk0
    fi
fi

if [ ! -d "/data/disk1" ]; then
    mkdir -p /data/disk1 >& /dev/null
    mkfs.ext4 -F $DISK1
    mount $DISK1 /data/disk1
    chmod 1777 /data/disk1
else
    if ! grep -Fq $DISK1 /proc/mounts ; then
	mount $DISK1 /data/disk1
	chmod 1777 /data/disk1
    fi
fi

if [ ! -d "/data/disk2" ]; then
    mkdir -p /data/disk2 >& /dev/null
    mkfs.ext4 -F $DISK2
    mount $DISK2 /data/disk2
    chmod 1777 /data/disk2
else
    if ! grep -Fq $DISK2 /proc/mounts ; then
	mount $DISK2 /data/disk2
	chmod 1777 /data/disk2
    fi
fi

if [ ! -d "/data/disk0/hdfs" ]; then
    mkdir /data/disk0/hdfs
fi

if [ ! -d "/data/disk0/spark-tmp" ]; then
    mkdir /data/disk0/spark-tmp
fi

if [ ! -d "/data/disk1/hdfs" ]; then
    mkdir /data/disk1/hdfs
fi

if [ ! -d "/data/disk1/spark-tmp" ]; then
    mkdir /data/disk1/spark-tmp
fi

if [ ! -d "/data/disk2/hdfs" ]; then
    mkdir /data/disk2/hdfs
fi

if [ ! -d "/data/disk2/spark-tmp" ]; then
    mkdir /data/disk2/spark-tmp
fi

chmod 1777 /data/disk0/hdfs
chmod 1777 /data/disk1/hdfs
chmod 1777 /data/disk2/hdfs
chmod 1777 /data/disk0/spark-tmp
chmod 1777 /data/disk1/spark-tmp
chmod 1777 /data/disk2/spark-tmp

if ! grep -Fq $DISK0 /etc/fstab ; then
    echo -e "$DISK0        /data/disk0     ext4    defaults,relatime       0       0" >> /etc/fstab
fi

if ! grep -Fq $DISK1 /etc/fstab ; then
    echo -e "$DISK1        /data/disk1     ext4    defaults,relatime       0       0" >> /etc/fstab
fi

if ! grep -Fq $DISK2 /etc/fstab ; then
    echo -e "$DISK2        /data/disk2     ext4    defaults,relatime       0       0" >> /etc/fstab
fi

systemctl unmask systemd-timesyncd
systemctl enable systemd-timesyncd.service
timedatectl set-ntp true
systemctl restart systemd-timesyncd.service

# Install software
rm -rf /var/lib/apt/lists/*
apt-get clean
apt-get update
SOFTWARE="nano sshpass unzip python3-venv python-apt-common fdisk dnsutils dos2unix whois nfs-common openjdk-21-jdk systemd-timesyncd"
echo "==> Installing software packages..."
if ! apt-get install -y -qq $SOFTWARE > /tmp/apt.log 2>&1; then
    echo "Error when installing software, log:"
    cat /tmp/apt.log
    exit 1
fi
echo "==> done"

# .profile
if ! grep -q "PATH=/sbin:\$PATH" /home/vagrant/.profile; then
  echo 'export PATH=/sbin:$PATH' >> /home/vagrant/.profile
fi

# NFS and SSH keys setup
SSH_PUBLIC_KEY=/share/.id_rsa.pub
SSH_DIR=/home/vagrant/.ssh
mkdir -p $SSH_DIR
chmod 700 $SSH_DIR

if [ ! -d "/share" ]; then
    mkdir /share >& /dev/null
fi

if grep -Fq /share /etc/fstab ; then
    sed -i "/share/d" /etc/fstab
fi

if [ "$CURRENT_HOST" = "$MASTER_HOSTNAME" ]; then
    # Install NFS server
    echo "==> Installing and configuring NFS server on $CURRENT_HOST..."
    if ! apt-get install -y -qq nfs-kernel-server >/tmp/apt.log 2>&1; then
    	echo "Error when installing software, log:"
    	cat /tmp/apt.log
    	exit 1
    fi
    echo "==> done"

    if [ ! -f $SSH_DIR/id_rsa.pub ]; then
	# Create ssh keys
	echo -e 'y\n' | sudo -u vagrant ssh-keygen -t rsa -f $SSH_DIR/id_rsa -q -N ''

	if [ ! -f $SSH_DIR/id_rsa.pub ]; then
		echo "SSH public key could not be created"
		exit -1
	fi
    fi

    if [ ! -f /etc/ssh/ssh_config.d/90-key-checking.conf ]; then
        cat > /etc/ssh/ssh_config.d/90-key-checking.conf << EOF
Host *
    StrictHostKeyChecking no
EOF
    fi

    chown vagrant:vagrant $SSH_DIR/id_rsa*
    cp $SSH_DIR/id_rsa.pub $SSH_PUBLIC_KEY

    # Configure NFS export
    chmod 1777 /share
    sed -i "/share/d" /etc/exports
    echo -e "/share        192.168.56.0/24(rw,sync,no_subtree_check)" >> /etc/exports
    exportfs -ra
else
    sed -i '/127.0.1.1.*-worker/d' /etc/hosts
    umount /share >& /dev/null || true
    if ! grep -Fq /share /etc/fstab ; then
        echo -e "$MASTER_HOSTNAME:/share        /share     nfs    nfsvers=4.2,defaults,relatime,_netdev       0       0" >> /etc/fstab
    fi
    
    systemctl daemon-reload
    sleep 1
    echo "Mounting NFS export on $CURRENT_HOST"
    mount /share
fi

if [ ! -f $SSH_PUBLIC_KEY ]; then
	echo "SSH public key does not exist"
	exit -1
fi

touch $SSH_DIR/authorized_keys 2>/dev/null
grep -q -f $SSH_PUBLIC_KEY $SSH_DIR/authorized_keys || cat $SSH_PUBLIC_KEY >> $SSH_DIR/authorized_keys
chown vagrant:vagrant $SSH_DIR/authorized_keys
chmod 0600 $SSH_DIR/authorized_keys
