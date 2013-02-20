# Copyright 2010 Jim Bridgewater

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# 12/27/10 Jim Bridgewater
# Added figure parameter to read function so update_graph function can
# use it.

# 05/31/10 Jim Bridgewater
# Added serial port auto detection

# 07/02/08 Jim Bridgewater
# Added a check to make sure set_voltage_source does not accept values
# with a precision greater than 50 mV.

# 06/19/08 Jim Bridgewater
# Imported the class named Error to pass error messages to the user
# interface.

# 06/16/08 Jim Bridgewater
# Fixed a bug in read that prevented sample_time from working
# properly when only one sample was requested.

# 06/04/08 Jim Bridgewater
# Modified to conform with PEP8 python style guide.

# 04/28/08 Jim Bridgewater
# Created this module to encapsulate the functions required to control
# the Keithley617.

# 04/11/08 Jim Bridgewater
# Implemented different holdoff values in read.  Added a
# a check to make sure the Keithley 617 is turned on.  Added arrays
# to store the I-V data.  Added placeholder for supporting ports
# other than COM4.  Added code to save the I-V data to a file.

# 04/10/08 Jim Bridgewater
# Added exception handlers for failure to open the serial port and 
# general exception handlers to make sure the Keithley's power supply
# is turned off and the serial port is closed before the program exits.
# Also added functions for writing to and reading from the Keithley.

# 04/04/08 Jim Bridgewater
# This program controls the Keithley 617 in order to measure I-V curves.
# It communicates with the Keithley via the Prologix USB-GPIB
# interface.  It assumes that the virtual serial port of the Prologix's FTDI 
# driver is COM? (see open_serial_port function below).


#################################################################
# The user functions defined in this module are:
#################################################################
# close_connection():
# current_mode():
# disable_voltage_source():
# display_voltage_source():
# enable_live_readings():
# enable_voltage_source():
# open_connection():
# read(interval = 0, samples = 1):
# resistance_mode():
# set_voltage_source(voltage):
# voltage_mode():

#################################################################
# Import libraries
#################################################################
import time
import prologixGPIBUSB as gpib
from errors import Error

#################################################################
# Global Declarations
#################################################################
Debug = 0  # set to 1 to enable printing of error codes

#################################################################
# Function definitions
#################################################################

# Close the connection to the Keithley 617.
def close_connection():
  gpib.close_connection()


# Set the Keithley to measure current.
def current_mode():
  gpib.write("F1X")
  time.sleep(1)


# Disable the output of the Keithley's internal voltage source.
def disable_voltage_source():
  gpib.write("O0X")


# Tell the Keithley to display the value of its internal voltage source.
def display_voltage_source():
  gpib.write("D1X")


# This function is a placeholder to maintain compatibility with the 
# keithley2400 module.
def enable_live_readings():
  pass


# Enable the output of the Keithley's internal voltage source.
def enable_voltage_source():
  gpib.write("O1X")


# Open the virtual serial port created by the Prologix USB/GPIB interface 
# and configure it to communicate with the Keithley 617.
def open_connection():
  gpib.open_connection()
  gpib.write("++addr 27")           # set GPIB address to the Keithley 617
  gpib.clear_selected_device()      # Reset Keithley
  gpib.write("C0X")                 # turn off zero check
  gpib.write("C0X")                 # again, just to make sure :)
  reading = gpib.readline()         # make sure Keithley's turned on 
  if not "DC" in reading:
    raise Error("ERROR: The Keithley 617 is not responding, make "\
    "sure it is turned on.")
    

# This function is the default value of the function parameter for the
# Read function below.
def do_nothing(dummy1, dummy2, dummy3):
  pass


# This function is called by the read function in the event that 
# samples > 1.
def read_multiple(interval = 0, samples = 1, update_graph = do_nothing, *args):
  if interval not in [0, 1, 10, 60, 600, 3600]:
    raise Error("ERROR: The Keithley 617 allows interval values of " + \
    "0, 1, 10, 60, 600, and 3600")
  if samples > 100:
    raise Error("ERROR: The Keithley 617 allows a maximum of 100 samples.")
  #gpib.flushInput()            # discard any previous readings
  if interval == 0:
    gpib.write("B1Q0G2X")      # store data as fast as possible
  elif interval == 1:
    gpib.write("B1Q1G2X")      # store data every 1 s
  elif interval == 10:
    gpib.write("B1Q2G2X")      # store data every 10 s
  elif interval == 60:
    gpib.write("B1Q3G2X")      # store data every 60 s
  elif interval == 600:
    gpib.write("B1Q4G2X")      # store data every 600 s
  elif interval == 3600:
    gpib.write("B1Q5G2X")      # store data every 3600 s
  else:
    raise Error("ERROR: The Keithley 617 allows sample intervals of " + \
    "0, 1, 10, 60, 600, or 3600 seconds.")
  Time = []
  Data = []
  CurrentSample = 1
  time.sleep(interval)
  Datum = gpib.readline()
  while CurrentSample <= samples:
    if ",%03d" % CurrentSample in Datum:
      Data = Data + [float(Datum[4:Datum.find(',')])]
      if interval == 0:
        # Keithley617 manual page 3-24
        Time = Time + [(CurrentSample - 1) * 0.360]    
      else:
        Time = Time + [(CurrentSample - 1) * interval]
      CurrentSample = CurrentSample + 1
      # call graph update function 
      update_graph(Time[-1], Data[-1], *args)
      time.sleep(interval)
    elif ",%03d" % (CurrentSample -1) in Datum:
      time.sleep(interval)
    gpib.write("B1X")        # get a reading
    Datum = gpib.readline()
  gpib.write("Q7X")          # turn off data storage
  return Time, Data


# This function is called by the read function in the event that 
# samples = 1.
def read_one(interval = 0):
  if interval == 0:
    gpib.write("B1Q0G2X")      # store data as fast as possible
  elif interval == 1:
    gpib.write("B1Q1G2X")      # store data every 1 s
  elif interval == 10:
    gpib.write("B1Q2G2X")      # store data every 10 s
  elif interval == 60:
    gpib.write("B1Q3G2X")      # store data every 60 s
  elif interval == 600:
    gpib.write("B1Q4G2X")      # store data every 600 s
  elif interval == 3600:
    gpib.write("B1Q5G2X")      # store data every 3600 s
  else:
    raise Error("ERROR: The Keithley 617 allows sample intervals of " + \
    "0, 1, 10, 60, 600, or 3600 seconds.")
  #gpib.flushInput()            # discard any previous readings
  samples = 2
  Data = []
  CurrentSample = 1
  Datum = gpib.readline()
  while CurrentSample <= samples:
    if ",%03d" % CurrentSample in Datum:
      Data = Data + [float(Datum[4:Datum.find(',')])]
      CurrentSample = CurrentSample + 1
      time.sleep(interval)
    elif ",%03d" % (CurrentSample -1) in Datum:
      time.sleep(interval)
    gpib.write("B1X")        # get a reading
    Datum = gpib.readline()
  gpib.write("Q7X")          # turn off data storage
  return Data[-1]


# This function reads values from the Keithley at a specified sample interval
# (in seconds). All timing is controlled by the Keithley. If only one sample 
# is requested the function returns the second sample taken by the Keithley, 
# otherwise it returns the first n samples.
# For example, Read(10) returns one sample that is taken 10 seconds after the
# function is called while Read(10, 2) returns two samples, the first one is 
# taken immediately when the function is called and the second sample is taken
# 10 seconds later.
# If more than one sample is requested, the allowed values of the interval 
# parameter are 0, 1, 10, 60, 600, and 3600. If only one sample is requested,
# the allowed values of interval are 0 through 99.
# The allowed values of the samples parameter are 1 to 100.
def read(interval = 0, samples = 1, update_graph = do_nothing, *args):
  if samples > 1:
    return read_multiple(interval, samples, update_graph, figure)
  else:
    return read_one(interval)


# Set the Keithley to measure resistance.
def resistance_mode():
  gpib.write("F2X")
  time.sleep(1)


# Set the value of the Keithley's internal voltage source.
def set_voltage_source(voltage):
  if abs((voltage / 0.05) - round(voltage / 0.05)) > 1e-10:
    print 'Warning: The voltage source in the Keithley 617 has a ' \
    'maximum resolution of 50 mV.'
  gpib.write("V" + "%.2f" % voltage + "X")


# Set the Keithley to measure voltage.
def voltage_mode():
  gpib.write("F0X")
  time.sleep(1)


# This function writes command codes to the Keithley.  For debugging
# purposes, it can also read the Keithley's error status conditions
# and print them if an error occurs.  Note that reading the error
# codes requires flushing any data from the serial input buffer - 
# therefore any data from read commands is lost.
#def write(command_code):
  #gpib.write(command_code + "\r\n")    # write command code
  #if Debug:
    #gpib.flushInput()          # discard any data
    #gpib.write("U1X")        # read the error conditions
    #error_code = gpib.readline()
    #if not "617000000000" in error_code:
      #raise Error("Keithley error " + error_code + \
      #"after command code" + command_code)


