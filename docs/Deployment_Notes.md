# **DAQ App - Deployment Notes**

## **Server Setup**

Using Ubuntu Server 22.04

### **Install Updates and Distribution Packages**

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y unixodbc unixodbc-dev python-is-python3
```

### **Install Additional Packages**
```cd``` into the app directory
```bash
sudo dpkg -i debs/msodbcsql17*
```

<br />

## **Application Setup**

### **Setup Virtual Environment**
```cd``` into the app directory.
```bash
python -m venv env
source env/bin/activate
pip install --upgrade pip
pip install wheel
pip install -r requirements.txt
deactivate
```

### **Setup Services**
While still in the app directory, copy all service files to /lib/systemd/system and enable them.
```bash
sudo cp system_files/service_files/* /lib/systemd/system/
sudo systemctl daemon-reload
```
Enable each service file using its correct name. Repeat this for each file.
```bash
sudo systemctl enable daq-pm0000.service
```
You can start the services immediately if you wish.
```bash
sudo systemctl enable --now daq-pm0000.service
```

### **Setup Log Rotation**
While still in the app directory, copy all logrotate config files to /etc/logrotate.d and set the proper ownership and permissions.
```bash
sudo cp system_files/logrotate/* /etc/logrotate.d/
sudo chown root.root /etc/logrotate.d/
sudo chmod 644 /etc/logrotate.d/
```

### **Copy Maintenance Scripts**
Install maintenance scripts. This list may vary.
```bash
sudo cp service_files/scripts/restart_daq_services.sh /usr/local/bin
sudo chmod +x /usr/local/bin/restart_daq_services.sh
```
