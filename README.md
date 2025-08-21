# ups2mqtt
Publishing the information of a Vultech UPS that uses the RichComm PowerManager II Protocol

The Vultech UPS1400VA-LFP comes with the RichComm PowerManager II program. However this program does not provide for any commmunication to a Home Automation system. Thanks to sites like https://github.com/networkupstools/nut I was able to find information to access the UPS via USB and theerafter to decode the relevant parts of the protocol with WireShark. 

It turns out to be a rather simple protocol although the learning curve for accessing a USB device in Python was rather steep.
Only 4 commands are needed and in fact it could also be done with only one command, the Q1 command.
The structure of the comamnds is:
Header Byte (1010 111 High order 2 bits + length) + data + \r
Q1    request Data Packet
I     request Version
F     request Specificaton
T01   request Test for 1 minute

The response to each command are:

Q1: Length = 47, Bitmap = 00101000:

LB240.0 000.0 241.0 000 49.0 14.2 30.8 00001000cr (L: Length, B: Bitmap)

The values are in plain text and represent in order:
- Input Voltage
- Load (this particular UPS does not seem to provide the laod)
- Output Voltage
- ??
- Frequency
- Battery Voltage
- Temperature ((for this UPS always 30.8)
- Bitmap First 0 becomes 1 when the power cuts off, sixth 0 becomes 1 while in test mode

I: Length = 39,Bitmap = 00100011:

LB                           V6.00     cr (L: Length, B: Bitmap)

F: Length = 22,Bitmap = 00100011:

LB220.0 003 12.00 50.0cr (L: Length, B: Bitmap)
