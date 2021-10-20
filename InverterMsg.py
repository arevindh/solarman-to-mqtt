import struct  # Converting bytes to numbers
import re
import binascii

# V5 table
offset = {
-1:  0, #len(1)
        #Inverter Data Address table
 0:  1, #Operating state
 1:  3, #Fault1
 2:  5, #Fault2
 3:  7, #Fault3
 4:  9, #Fault4
 5: 11, #Fault5
        #PV Input Message
 6: 13, #PV1 voltage Unit:0.1V
 7: 15, #PV1 current Unit:0.01A
 8: 17, #PV2 voltage Unit:0.1V
 9: 19, #PV2 current Unit:0.01A
10: 21, #PV1 power Unit:0.01kw
11: 23, #PV2 power Unit:0.01kw
        #Output Grid Message
12: 25, #Output active power Unit:0.01kW
13: 27, #Output reactive power Unit:0.01kVar
14: 29, #Grid frequency Unit:0.01Hz
15: 31, #A-phase voltage Unit:0.1V
16: 33, #A-phase current Unit:0.01A
17: 35, #B-phase voltage Unit:0.1V
18: 37, #B-phase current Unit:0.01A
19: 39, #C-phase voltage Unit:0.1V
20: 41, #C-phase current Unit:0.01A
        #Inverter Generation message
21: 43, #Total production hi Unit:1kWh
22: 45, #Total production low
23: 47, #Total generation hi Unit:1 hour
24: 49, #Total generation low
25: 51, #Today production Unit:0.01kWh
26: 53, #Today generation time Unit:1 Minute
        #Inverter inner message 
27: 55, #Inverter module temperature
28: 57, #Inverter inner temperature
29: 59, #Inverter Bus voltage Unit:0.1V
30: 61, #PV1 voltage sample by slave CPU Unit:0.1V
31: 63, #PV1 current sample by slave CPU Unit:0.01A
32: 65, #Count-down time
33: 67, #Inverter alert message
34: 69, #Input mode 0x00: in parallal 0x01: in dependent
35: 71, #Communication board inner message
36: 73, #Insulation of PV1+ to ground
37: 75, #Insulation of PV - to ground
38: 77, #Country
}

mode = ['Unknown', 'Check', 'Normal', 'Fault', 'Permanent' ]

class InverterMsg(object):
    """Decode the response message from an inverter logger."""
    msg_body = ""

    def __init__(self, msg, logger = "no"):
        self.raw_msg = msg
        self.msg_body = msg[27:]
        self.offset = offset

    def __get_string(self, begin, end):
        """Extract string from message.

        Args:
            begin (int): starting byte index of string
            end (int): end byte index of string

        Returns:
            str: String in the message from start to end
        """
        return self.msg_body[begin:end].decode('cp437')
#
    def __get_int(self, begin):
        """Extract byte value from message.

        Args:
            begin (int): starting byte index of string

        Returns:
            int: value at offset
        """
        if (len(self.msg_body) < begin):
            return 0
        return int(binascii.hexlify(bytearray(self.msg_body[begin:begin + 1])), 16)
#
    def __get_short(self, begin, divider=10):
        """Extract short from message.

        The shorts in the message could actually be a decimal number. This is
        done by storing the number multiplied in the message. So by dividing
        the short the original decimal number can be retrieved.

        Args:
            begin (int): index of short in message
            divider (int): divider to change short to float. (Default: 10)

        Returns:
            int or float: Value stored at location `begin`
        """
        num = struct.unpack('!H', self.msg_body[begin:begin + 2])[0]
        if num > 32767:
            return float(-(65536 - num)) / divider
        else:
            return float(num) / divider

    def __get_long(self, begin, divider=10):
        """Extract long from message.

        The longs in the message could actually be a decimal number. By
        dividing the long, the original decimal number can be extracted.

        Args:
            begin (int): index of long in message
            divider (int): divider to change long to float. (Default : 10)

        Returns:
            int or float: Value stored at location `begin`
        """
        return float(
            struct.unpack('!I', self.msg_body[begin:begin + 4])[0]) / divider

    ####################################################################################################################

    @property
    def len(self):
        """received data len msg."""
        return self.__get_int(offset[-1])

    @property
    def mode(self):
        """Operating mode."""
        return mode[int(self.__get_short(offset[0], 1))]


    def v_pv(self, i=1):
        """Voltage of PV input channel.

        Available channels are 1, 2; if not in this range the function will
        default to channel 1.

        Args:
            i (int): input channel (valid values: 1, 2)

        Returns:
            float: PV voltage of channel i
        """
        if i not in range(1, 3):
            i = 1
        num = offset[6] + (i - 1) * 4
        return self.__get_short(num)

    def i_pv(self, i=1):
        """Current of PV input channel.

        Available channels are 1, 2; if not in this range the function will
        default to channel 1.

        Args:
            i (int): input channel (valid values: 1, 2)

        Returns:
            float: PV current of channel i
        """
        if i not in range(1, 3):
            i = 1
        num = offset[7] + (i - 1) * 4
        return self.__get_short(num, 100)

    def p_pv(self, i=1):
        """Power of PV input channel.

        Available channels are 1, 2; if not in this range the function will
        default to channel 1.

        Args:
            i (int): input channel (valid values: 1, 2)

        Returns:
            float: PV current of channel i
        """
        if i not in range(1, 3):
            i = 1
        num = offset[10] + (i - 1) * 2
        return self.__get_short(num, 100)

    @property
    def output_active_power(self):
        """Output active power  kW"""
        return self.__get_short(offset[12], 100)  # Divide by 100

    @property
    def output_reactive_power(self):
        """Output reactive power kVar"""
        return self.__get_short(offset[13], 100)  # Divide by 100

    @property
    def e_today(self):
        """Energy generated by inverter today in kWh"""
        return self.__get_short(offset[25], 100)  # Divide by 100

    @property
    def e_total(self):
        """Total energy generated by inverter in kWh"""
        return self.__get_long(offset[21], 1)

    @property
    def h_total(self):
        """Hours the inverter generated electricity"""
        return int(self.__get_long(offset[23], 1))  # Don't divide


    @property
    def module_temp(self):
        """Temperature recorded by the module."""
        return self.__get_short(offset[27], 1)

    @property
    def inner_temp(self):
        """Temperature recorded by the inverter."""
        return self.__get_short(offset[28], 1)

    def f_ac(self, i=1):
        """Frequency of the output channel

        Available channels are 1, 2 or 3; if not in this range the function will
        default to channel 1.

        Args:
            i (int): output channel (valid values: 1, 2, 3)

        Returns:
            float: AC frequency of channel i
        """
        #the same 4 all
        return self.__get_short(offset[14], 100)  # Divide by 100

    def v_ac(self, i=1):
        """Voltage of the Inverter output channel

        Available channels are 1, 2 or 3; if not in this range the function will
        default to channel 1.

        Args:
            i (int): output channel (valid values: 1, 2, 3)

        Returns:
            float: AC voltage of channel i
        """
        if i not in range(1, 4):
            i = 1
        num = offset[15] + (i - 1) * 4
        return self.__get_short(num)

    def i_ac(self, i=1):
        """Current of the Inverter output channel

        Available channels are 1, 2 or 3; if not in this range the function will
        default to channel 1.

        Args:
            i (int): output channel (valid values: 1, 2, 3)

        Returns:
            float: AC current of channel i

        """
        if i not in range(1, 4):
            i = 1
        num = offset[16] + (i - 1) * 4
        return self.__get_short(num, 100)

    def p_ac(self, i=1):
        """Power output of the output channel

        Available channels are 1, 2 or 3; if no tin this range the function will
        default to channel 1.

        Args:
            i (int): output channel (valid values: 1, 2, 3)

        Returns:
            float: Power output of channel i
        """
        if i not in range(1, 4):
            i = 1
        return (self.v_ac(i) * self.i_ac(i)) / 1000

####################################################################################################################


    @property
    def msg(self):
        """received status msg."""
        return self.__get_string(offset[2], self.len+offset[2])

    @property
    def id(self):
        """ID of the inverter."""
        #return self.__get_string(offset[3], offset[3]+16).lstrip().rstrip() #Strip spaces from shorter or padded inverter SN
        return "?"

    @property
    def GVFaultValue(self):
        """Grid voltage fault value in V"""
        return self.__get_short(offset[15], 10)  # Divide by 10

    @property
    def GVFaultValue(self):
        """Grid frequency fault value in Hz"""
        return self.__get_short(offset[16], 100)  # Divide by 100

    @property
    def GZFaultValue(self):
        """Grid impedance fault value in Ohm"""
        return self.__get_short(offset[17], 1000)  # Divide by 1000

    @property
    def TmpFaultValue(self):
        """Temperature fault value in oC"""
        return self.__get_short(offset[18], 10)  # Divide by 10

    @property
    def PVFaultValue(self):
        """PV voltage fault value in V"""
        return self.__get_short(offset[19], 10)  # Divide by 10

    @property
    def GFCIFaultValue(self):
        """GFCI current fault value in A"""
        return self.__get_short(offset[20], 1000)  # Divide by 1000

    @property
    def errorMsg(self):
        """errorMsg binary index value"""
        return int(self.__get_long(offset[21]))

    @property
    def main_fwver(self):
        """Inverter main firmware version."""
        if (self.__get_int(offset[22]) == 0): return ""
        return re.sub('[^\x20-\x7f]', '', self.__get_string(offset[22], offset[22]+19))

    @property
    def slave_fwver(self):
        """Inverter slave firmware version."""
        if (self.__get_int(offset[23]) == 0): return ""
        return re.sub('[^\x20-\x7f]', '', self.__get_string(offset[23], offset[23]+19))
