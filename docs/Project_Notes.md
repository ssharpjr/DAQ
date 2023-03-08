# **DAQ Loop Documentation**

## **Pre-Loop** 

*(Runs only on startup)*

### **Pre-Loop: Verify the DAQ box is on**

- Ping the DAQ box (single ping with 3 sec timeout).
  - If ping succeeds, then continue
  - Else, pause for 10 seconds and try again

### **Pre-Loop: Get/Set current extruder counts**

#### Extruder Counts

- **(exc_box_last, exe2_box_last)** - Get the current exc and exe2 counts from the DAQ box.
- **(exc_db_last, exe2_db_last)** - Get the last exc and exe2 records from the DB by device ID and date.
- **(exc_db_max, exe2_db_max)** - Get the MAX(exc) and MAX(exe2) records from the DB by device ID.
- Wait for a few seconds to allow the DAQ extruder counts to increment a few times.
- **(exc_box_current, exe2_box_current)** - Get the current exc and exe2 counts from the DAQ box again *(This creates a time delta)*.

#### Calculate

- Get deltas
  - ```exc_box_delta = exc_box_current - exc_box_last```
  - ```exe2_box_delta = exe2_box_current - exe2_box_last```
- Set new counts *(Use the MAX counts to set the initial 'new' counts)*
  - ```new_exc = exc_db_max + exc_box_delta```
  - ```new_exe2 = exe2_db_max + exe2_box_delta```
- Reset 'last' variables *(Use the 'new' counts to set the 'last' counts)*
  - ```exc_box_last = exc_box_current```
  - ```exe2_box_last = exe2_box_current```
  - ```exc_db_last = new_exc```
  - ```exe2_db_last = new_exe2```

## **Loop**

### Loop: Verify the DAQ box is still on

- Ping the DAQ box (single ping with 3 sec timeout).
  - If ping succeeds, then continue
  - Else, pause for 10 seconds and try again

### Loop: Main Loop Runs

- Calculate Deltas *(repeat for exc, exe2, mnc)*
  - Use existing 'last' variables
  - Get current DAQ box variables (exc, exe2, mnc)
  - if ```current exc >= last exc``` (DAQ has not rebooted),
    - then  
      - ```exc delta = current exc - last exc```
    - else (the DAQ box has rebooted so use the current exc)
      - ```exc delta = current exc```
- Calculate new exc/exe2/mnc
  - ```new exc = max db exc + exc delta```
- Save new exc as the new 'last' exc to use on the next loop
  - ```last exc = new exc```
- Write data to the DB