import sys
import glob
import serial
import io
import time
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import logging
import AFEregisters

import pdb

WRITE_REG = 0x02
READ_REG = 0x03
READ_ADC = [0x01, 0x2A]
STOP_ADC = [0x06, 0x0D]
DEVICE_ID = 0x04
TERMINATE = 0x0D
ADDR_SIZE = 2
REG_SIZE = 6
ADC_COMMAND_SIZE = 8
ADC_RESPONSE_SIZE = 22
TWOS_COMPLEMENT_SIZE = 22
CHECK_BIT=1<<(TWOS_COMPLEMENT_SIZE-1)
SIZE_SUBTRACT=0b111<<(TWOS_COMPLEMENT_SIZE-1)
RESOLUTION=1<<(TWOS_COMPLEMENT_SIZE)-1

ASCII_DICT = {
    0 : 0x30,
    1 : 0x31,
    2 : 0x32,
    3 : 0x33,
    4 : 0x34,
    5 : 0x35,
    6 : 0x36,
    7 : 0x37,
    8 : 0x38,
    9 : 0x39,
    10 : 0x61,
    11 : 0x62,
    12 : 0x63,
    13 : 0x64,
    14 : 0x65,
    15 : 0x66
}

OFFDAC_RANGE_DICT = {
    0 : 0b000,
    1 : 0b011,
    2 : 0b101,
    3 : 0b111
}

class AFEBoard ():
    def __init__(self, port):
        self.port = port
        self.serial_stream = serial.Serial(self.port, 115200, timeout=None)
        self.timing_frequency = 250
        self.register_state = self.read_all_registers()
        if not self.serial_stream.is_open:
            print("Error!! Could not open port.")

    def open_port(self):
        self.serial_stream = serial.Serial(self.port, 115200, timeout=None)
        if not self.serial_stream.is_open:
            print("Error!! Could not open port.")

    def close_port(self):
        self.serial_stream.close()

    def is_port_open(self):
        return self.serial_stream.is_open


    def send_receive(self, command, no_bytes):
        print("Command: ",command)
        self.serial_stream.write(command)
        if not no_bytes:
            return bytearray([0])
        else:
            bytes_read = self.serial_stream.read(no_bytes)
            #if self.serial_stream.out_waiting != 0:
            #    raise Exception('Not enough bytes read from serial')
            #if (no_bytes > 10):
            #    self.serial_stream.write(STOP_ADC)
            #    print(command)
            #    self.close_port()
            #    time.sleep(0.5)
            #    self.open_port()
            return bytes_read

    def encode_value(self, value, no_bytes):
        bytes_array = []
        for single_byte in range(no_bytes-1,-1,-1):
            bytes_array.append(ASCII_DICT[((value >> 4*single_byte) & 0xF)])
        return bytes_array

    def parse_read_value(self, bytes_array):
        readable_array = list(bytes_array)
        register_value = readable_array[2] + (readable_array[3]<<8) + (readable_array[4]<<16)
        return register_value

#AFE4900EVM register read
    def read_register(self, address):
        address_bytes = self.encode_value(address,ADDR_SIZE)
        byte_command = [READ_REG]
        byte_command.extend(address_bytes)
        byte_command.append(TERMINATE)
        #Returned message is 7 bytes long
        bytes_read = self.send_receive(byte_command, 7)
        value = self.parse_read_value(bytes_read)
        return value

    def read_all_registers(self):
        reg_values = AFEregisters.ALL_REGS_DICT
        for key in reg_values:
            reg_values[key] = self.read_register(key)
        return(reg_values)

#AFE4900EVM register write
    def write_register(self, address, value):
        byte_address = self.encode_value(address,ADDR_SIZE)
        byte_value = self.encode_value(value,REG_SIZE)
        byte_command = [WRITE_REG]
        byte_command.extend(byte_address)
        byte_command.extend(byte_value)
        byte_command.append(TERMINATE)
        self.send_receive(byte_command, 0)
        self.register_state[address] = value
        time.sleep(0.001)

#Read finite amount of ADC samples
    def parse_adc_values(self, bytes_array, no_samples):
        def convert(val):
            if val & CHECK_BIT !=0:
                val = -(val-SIZE_SUBTRACT)
                # print(val) # Special Twos Complement where subtract by 0b111 << 22-1 positive returned as is
            return (val*1.2/RESOLUTION)
            # Convert from 21 bit number to voltage -1.2<out<1.2
        def LED_values(row):
            #print(row)
            final_list = np.zeros(6)
            for LED_pos in range(6):
                final_list[LED_pos] = convert((row[LED_pos*3+2] + (row[LED_pos*3+3]<<8) + (row[LED_pos*3+4]<<16)))
            return final_list

        byte_list = np.split(np.array(list(bytes_array)),no_samples)
        #print(byte_list)
        PPG_values = np.array(list(map(lambda x: LED_values(x), byte_list)))
        return PPG_values

    # def parse_adc_values2(self, bytes_array, no_samples):
    #     def twos_comp(val, bits):
    #         print("val: ",val)
    #         print("bits: ",bits)
    #
    #     def LED_values(row):
    #         #print(row)
    #

    def finite_adc_read(self, no_samples):
        byte_value = self.encode_value(no_samples, ADC_COMMAND_SIZE)
        byte_command = READ_ADC
        byte_command = byte_command + byte_value
        byte_command.append(TERMINATE)
        bytes_read = self.send_receive(byte_command, no_samples*ADC_RESPONSE_SIZE)
        return self.parse_adc_values(bytes_read, no_samples)

    def stop_adc_read(self):
        self.send_receive(STOP_ADC, 0)

    def start_adc_read(self):
        byte_value = self.encode_value(0, ADC_COMMAND_SIZE)
        byte_command = READ_ADC
        byte_command = byte_command + byte_value
        byte_command.append(TERMINATE)
        bytes_read = self.send_receive(byte_command, 0)

    def adc_unlimited_read(self, samples):
        bytes_read = self.serial_stream.read(samples*ADC_RESPONSE_SIZE)
        out = self.parse_adc_values(bytes_read, samples)
        return out

#Function to set-up LED currents
#Each LED contains a touple (en,val), where en is saying if the LED value should be modified and val the desired value in mA.
#Max is either 1(100mA) or 0(50mA)
    def set_LED_currents(self, led1, led2, led3, led4, max_100):
        #pdb.set_trace()
        old_config = self.register_state[AFEregisters.CTRL_TXCURR_OSC]
        #print(hex(old_config))
        current_step_size = 255.0/50.0
        if max_100:
            current_step_size = 255.0/100.0
            new_config = (old_config | 0x020000)
        else:
            new_config = (old_config & ~0x020000)
        new_config = (new_config & 0xFFFFFF)

        old_led123_config = self.register_state[AFEregisters.LED123CURRENT]

        #turn LEDs off
        if (led4[0]):
            self.write_register(AFEregisters.LED4CURRENT,0)
            time.sleep(0.01)

        self.write_register(AFEregisters.LED123CURRENT,0)
        time.sleep(0.01)

        #write correct current setting
        self.write_register(AFEregisters.CTRL_TXCURR_OSC,new_config)
        time.sleep(0.01)

        #Populate the bit groups for LED1
        if led1[0]:
            binary_val = int(current_step_size*led1[1]) & 0xFF
            #print("First LED value: " + str(binary_val))
            led1_lower_bits = binary_val & 0x3
            led1_upper_bits = (binary_val >> 2)
        else:
            led1_lower_bits = (old_led123_config >> 18) & 0x3
            led1_upper_bits = old_led123_config & 0x3F
        #Populate the bit groups for LED2
        if led2[0]:
            binary_val = int(current_step_size*led2[1]) & 0xFF
            #print("Second LED value: " + str(binary_val))
            led2_lower_bits = binary_val & 0x3
            led2_upper_bits = (binary_val >> 2)
        else:
            led2_lower_bits = (old_led123_config >> 20) & 0x3
            led2_upper_bits = (old_led123_config >> 6) & 0x3F
        #Populate the bit groups for LED3
        if led3[0]:
            binary_val = int(current_step_size*led3[1]) & 0xFF
            #print("Third LED value: " + str(binary_val))
            led3_lower_bits = binary_val & 0x3
            led3_upper_bits = (binary_val >> 2)
        else:
            led3_lower_bits = (old_led123_config >> 22) & 0x3
            led3_upper_bits = (old_led123_config >> 12) & 0x3F
        #Construct and update the new led123 config
        new_led123_config = (led1_upper_bits + (led2_upper_bits << 6) + (led3_upper_bits << 12) + (led1_lower_bits << 18) + (led2_lower_bits << 20) + (led3_lower_bits << 22)) & 0xFFFFFF
        #print(hex(new_led123_config))
        self.write_register(AFEregisters.LED123CURRENT, new_led123_config)
        time.sleep(0.01)
        #time.sleep(1)

        #Only if LED4 has enabled config prepare the word and send it
        if led4[0]:
            binary_val = int(current_step_size*led4[1]) & 0xFF
            led4_lower_bits = binary_val & 0x3
            led4_upper_bits = (binary_val >> 2)
            new_led4_config = ((led4_lower_bits << 9) + (led4_upper_bits << 11)) & 0x01FE00
            #print(hex(new_led4_config))
            self.write_register(AFEregisters.LED4CURRENT, new_led4_config)
            time.sleep(0.01)

#Setup the feedback resistor and capacitor values and number of active phases.
#Active phases can be either 1,2 or 4.
#Feedback values is a list of touples in the form of [(Rf1, Cf1), (Rf2, Cf2), ...] with Rf having value from 0-8 and Cf 0-7.
#When all 4 require different setting, the settings should be in order of LED1, LED2, LED3, Amb1

    def set_feedback_gains(self, active_phases, feedback_vals):
        SEP_GAIN_FLAGS = [0,0]
        if (active_phases in [1,2,4]):
            SEP_GAIN_FLAGS[0] = (active_phases & 0x2) >> 1
            SEP_GAIN_FLAGS[1] = (active_phases & 0x4) >> 2
        else:
            raise Exception("Wrong number of active phases for feedback gain settings")
        if SEP_GAIN_FLAGS[1]:
            #Set the SEP4 flag
            old_config = self.register_state[AFEregisters.CTRL_TXCURR_OSC]
            new_config = (old_config | 0x008000)
            self.write_register(AFEregisters.CTRL_TXCURR_OSC,new_config)
            time.sleep(0.01)
            if (len(feedback_vals)==4):
                for fdb in feedback_vals:
                    #print(fdb)
                    if(fdb[0] > 8 or fdb[1] > 7):
                        raise Exception("Invalid feedback resistor or capacitor setting (%d,%d)" % (fdb[0], fdb[1]))
            else:
                raise Exception("Wrong number feedback values provided")
            old_gain1_reg = self.register_state[AFEregisters.FEEDBACK_GAIN1]
            new_gain1_reg = ((old_gain1_reg & 0xFFFF00) + (feedback_vals[0][1] << 3) + (feedback_vals[0][0] & 0x7) + ((feedback_vals[0][0] & 0x8) << 3)) & 0xFFFFFF
            self.write_register(AFEregisters.FEEDBACK_GAIN1,new_gain1_reg)
            time.sleep(0.01)
            new_gain2_reg = ((feedback_vals[1][1] << 3) + (feedback_vals[1][0] & 0x7) + ((feedback_vals[1][0] & 0x8) << 3)) & 0xFFFFFF
            self.write_register(AFEregisters.FEEDBACK_GAIN2,new_gain2_reg)
            time.sleep(0.01)
            new_gain34_reg = ((feedback_vals[2][1] << 3) + (feedback_vals[2][0] & 0x7) + ((feedback_vals[2][0] & 0x8) << 3) + (feedback_vals[3][1] << 11) + ((feedback_vals[3][0] & 0x7) << 8) + ((feedback_vals[3][0] & 0x8) << 11))
            self.write_register(AFEregisters.FEEDBACK_GAIN34,new_gain34_reg)
            time.sleep(0.01)

            #print("Old config = %x, New config = %x,\nOld gain1 reg = %x, Gain1 reg = %x,\nGain2 reg = %x,\nGain34 reg = %x" % (old_config, new_config, old_gain1_reg, new_gain1_reg, new_gain2_reg, new_gain34_reg))

        elif SEP_GAIN_FLAGS[0]:
            #Reset the SEP4 flag
            old_config = self.register_state[AFEregisters.CTRL_TXCURR_OSC]
            new_config = (old_config & ~0x008000)
            self.write_register(AFEregisters.CTRL_TXCURR_OSC,new_config)
            time.sleep(0.01)
            if (len(feedback_vals) == 2):
                for fdb in feedback_vals:
                    if(fdb[0] > 8 or fdb[1] > 7):
                        raise Exception("Invalid feedback resistor or capacitor setting (%d,%d)" % (fdb[0], fdb[1]))
            else:
                raise Exception("Wrong number feedback values provided")
            old_gain1_reg = self.register_state[AFEregisters.FEEDBACK_GAIN1]
            new_gain1_reg = ((old_gain1_reg & 0xFFFF00) + (feedback_vals[0][1] << 3) + (feedback_vals[0][0] & 0x7) + ((feedback_vals[0][0] & 0x8) << 3)) & 0xFFFFFF
            self.write_register(AFEregisters.FEEDBACK_GAIN1,new_gain1_reg)
            time.sleep(0.01)
            new_gain2_reg = (0x008000 + (feedback_vals[1][1] << 3) + (feedback_vals[1][0] & 0x7) + ((feedback_vals[1][0] & 0x8) << 3)) & 0xFFFFFF
            self.write_register(AFEregisters.FEEDBACK_GAIN2,new_gain2_reg)
            time.sleep(0.01)

            #print("Old config = %x, New config = %x,\nOld gain1 reg = %x, Gain1 reg = %x,\nGain2 reg = %x" % (old_config, new_config, old_gain1_reg, new_gain1_reg, new_gain2_reg))
        else:
            #Reset the SEPGAIN4 flag
            old_config = self.register_state[AFEregisters.CTRL_TXCURR_OSC]
            new_config = (old_config & ~0x008000)
            self.write_register(AFEregisters.CTRL_TXCURR_OSC,new_config)
            time.sleep(0.01)
            if (len(feedback_vals) == 1):
                for fdb in feedback_vals:
                    if(fdb[0] > 8 or fdb[1] > 7):
                        raise Exception("Invalid feedback resistor or capacitor setting (%d,%d)" % (fdb[0], fdb[1]))
            else:
                raise Exception("Wrong number feedback values provided")
            old_gain1_reg = self.register_state[AFEregisters.FEEDBACK_GAIN1]
            new_gain1_reg = ((old_gain1_reg & 0xFFFF00) + (feedback_vals[0][1] << 3) + (feedback_vals[0][0] & 0x7) + ((feedback_vals[0][0] & 0x8) << 3)) & 0xFFFFFF
            self.write_register(AFEregisters.FEEDBACK_GAIN1,new_gain1_reg)
            time.sleep(0.01)
            #Reset the SEPGAIN flag
            self.write_register(AFEregisters.FEEDBACK_GAIN2,0)
            time.sleep(0.01)

    def set_BW_early_DAC(self, BW, earlyDAC_en):
        if BW in [0,1,2]:
            old_config_0 = self.register_state[AFEregisters.FEEDBACK_GAIN1]
            old_config_1 = self.register_state[AFEregisters.BW1_REG]
            if (BW & 1):
                old_config_0 |= (0x000200)
            else:
                old_config_0 &= ~(0x000200)
            self.write_register(AFEregisters.FEEDBACK_GAIN1,old_config_0)
            time.sleep(0.01)
            if ((BW>>1) & 1):
                old_config_1 |= (0x800000)
            else:
                old_config_1 &= ~(0x800000)
            self.write_register(AFEregisters.BW1_REG,old_config_1)
            time.sleep(0.01)
        else:
            raise Exception("Invalid filter BW setting provided")

        oldDAC_config = self.register_state[AFEregisters.OFFDAC_MID_SETTING]
        if (earlyDAC_en):
            oldDAC_config |= (0x100000)
        else:
            oldDAC_config &= ~(0x100000)
        self.write_register(AFEregisters.OFFDAC_MID_SETTING,oldDAC_config)
        time.sleep(0.01)

#Setup the offset DC current values
#Each current setting is a touple in form (en, curr_val, pol)
#en = 0,1; determines if the given LED current should be updated or not
#curr_val = 0-127; value of the current register setting
#pol = 0 (positive), 1 (negative); polarity of the given offset current
    def set_dc_current_offset(self, current_range, LED_currents):
        if current_range in [0,1,2,3]:
            old_config = self.register_state[AFEregisters.FEEDBACK_GAIN1]
            old_config &= 0x000FFF
            old_config += (OFFDAC_RANGE_DICT[current_range]<<12)
            self.write_register(AFEregisters.FEEDBACK_GAIN1,old_config)
            time.sleep(0.01)
        else:
            raise Exception("Invalid offdac current range specified")

        old_offdac_config_0 = self.register_state[AFEregisters.OFFDAC_MID_SETTING]
        old_offdac_config_1 = self.register_state[AFEregisters.OFFDAC_EXT_SETTING]

        if len(LED_currents) != 4:
            raise Exception("Wrong number of LED current provided, needs 4.")

        if (LED_currents[0][0]):
            LED1_LSB_EXT = (LED_currents[0][1] & 0x1)
            LED1_LSB = ((LED_currents[0][1] & 0x2) >> 1)
            LED1_MID = ((LED_currents[0][1] & 0x3C) >> 2)
            LED1_MSB = ((LED_currents[0][1] & 0x40) >> 6)
            LED1_POL = LED_currents[0][2] & 0x1
        else:
            LED1_LSB_EXT = (old_offdac_config_1 >> 9) & 0x1
            LED1_LSB = (old_offdac_config_1 >> 2) & 0x1
            LED1_MID = (old_offdac_config_0 >> 5) & 0xF
            LED1_MSB = (old_offdac_config_1 >> 3) & 0x1
            LED1_POL = (old_offdac_config_0 >> 9) & 0x1

        if (LED_currents[1][0]):
            LED2_LSB_EXT = (LED_currents[1][1] & 0x1)
            LED2_LSB = ((LED_currents[1][1] & 0x2) >> 1)
            LED2_MID = ((LED_currents[1][1] & 0x3C) >> 2)
            LED2_MSB = ((LED_currents[1][1] & 0x40) >> 6)
            LED2_POL = LED_currents[1][2] & 0x1
        else:
            LED2_LSB_EXT = (old_offdac_config_1 >> 11) & 0x1
            LED2_LSB = (old_offdac_config_1 >> 6) & 0x1
            LED2_MID = (old_offdac_config_0 >> 15) & 0xF
            LED2_MSB = (old_offdac_config_1 >> 7) & 0x1
            LED2_POL = (old_offdac_config_0 >> 19) & 0x1

        if (LED_currents[2][0]):
            LED3_LSB_EXT = (LED_currents[2][1] & 0x1)
            LED3_LSB = ((LED_currents[2][1] & 0x2) >> 1)
            LED3_MID = ((LED_currents[2][1] & 0x3C) >> 2)
            LED3_MSB = ((LED_currents[2][1] & 0x40) >> 6)
            LED3_POL = LED_currents[2][2] & 0x1
        else:
            LED3_LSB_EXT = (old_offdac_config_1 >> 8) & 0x1
            LED3_LSB = (old_offdac_config_1) & 0x1
            LED3_MID = (old_offdac_config_0) & 0xF
            LED3_MSB = (old_offdac_config_1 >> 1) & 0x1
            LED3_POL = (old_offdac_config_0 >> 4) & 0x1

        if (LED_currents[3][0]):
            LED4_LSB_EXT = (LED_currents[3][1] & 0x1)
            LED4_LSB = ((LED_currents[3][1] & 0x2) >> 1)
            LED4_MID = ((LED_currents[3][1] & 0x3C) >> 2)
            LED4_MSB = ((LED_currents[3][1] & 0x40) >> 6)
            LED4_POL = LED_currents[3][2] & 0x1
        else:
            LED4_LSB_EXT = (old_offdac_config_1 >> 10) & 0x1
            LED4_LSB = (old_offdac_config_1 >> 4) & 0x1
            LED4_MID = (old_offdac_config_0 >> 10) & 0xF
            LED4_MSB = (old_offdac_config_1 >> 5) & 0x1
            LED4_POL = (old_offdac_config_0 >> 14) & 0x1

        new_offdac_config_0 = (LED3_MID + (LED3_POL << 4) + (LED1_MID << 5) + (LED1_POL << 9) + (LED4_MID << 10) + (LED4_POL << 14) + (LED2_MID << 15) + (LED2_POL << 19) + (old_offdac_config_0 & 0xF00000)) & 0xFFFFFF
        #print(hex(new_offdac_config_0))
        self.write_register(AFEregisters.OFFDAC_MID_SETTING,new_offdac_config_0)
        time.sleep(0.01)

        new_offdac_config_1 = (LED3_LSB + (LED3_MSB << 1) + (LED1_LSB << 2) + (LED1_MSB << 3) + (LED4_LSB << 4) + (LED4_MSB << 5) + (LED2_LSB << 6) + (LED2_MSB << 7) + (LED3_LSB_EXT << 8) +
            (LED1_LSB_EXT << 9) + (LED4_LSB_EXT << 10) + (LED2_LSB_EXT << 11)) & 0xFFFFFF
        #print(hex(new_offdac_config_1))
        self.write_register(AFEregisters.OFFDAC_EXT_SETTING,new_offdac_config_1)
        time.sleep(0.01)

    def set_250Hz_timing(self, configuration):
        print("setting timing")
        #Make sure internal oscillator is enabled
        old_config = self.register_state[AFEregisters.CTRL_TXCURR_OSC]
        new_config = (old_config | 0x000200) & 0xFFFFFF
        self.write_register(AFEregisters.CTRL_TXCURR_OSC,new_config)
        time.sleep(0.01)
        for key in AFEregisters.TIMING_REGS_250Hz_DICT:
            register_config = AFEregisters.TIMING_REGS_250Hz_DICT[key]
            #print(register_config[0],register_config[1])
            self.write_register(register_config[0],register_config[1])
            time.sleep(0.01)
        if configuration == 'SFH7072':
            print("Setting up Timing for Default Sensor Board")
            self.write_register(AFEregisters.DUAL_PD_REG, 0x000008)
            #print("Setup IR cut photodiode for LED1 - green")
            self.write_register(AFEregisters.PD1STC, 0x000026)
            self.write_register(AFEregisters.PD1ENDC, 0x000041)
            self.write_register(AFEregisters.PD2STC, 0x000042)
            self.write_register(AFEregisters.PD2ENDC, 0x00004F)
            time.sleep(0.001)
            #self.set_LED_currents((1,15), (1,30), (1,45), (0,0), 1) #Set currents according to LED ratings
            #self.set_BW_early_DAC(0, 1)
            print("Timing set up  done")
        elif configuration == 'SFH7050':
            print("Setting up Timing for SFH7050 Sensor Board")

            self.write_register(AFEregisters.DUAL_PD_REG, 0x000000)
            self.write_register(AFEregisters.OSC_ENABLE, 0x000000)
            self.write_register(AFEregisters.CLOCK_FREQUENCY, 0x000004)
            self.write_register(AFEregisters.ENABLE_ULP, 0x000020)
            self.write_register(AFEregisters.INT_MUX1, 0x000000)
            self.write_register(AFEregisters.ENABLE_PD2_SHORT, 0x000010)

            #self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['CLKDIV2'][0], 0x000004)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['PRPCOUNT'][0],0x00003F)

            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED2LEDSTC'][0],0x00000A)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED2LEDENDC'][0],0x00000D)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED2STC'][0],0x00000B)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED2ENDC'][0],0x00000D)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED2CONVST'][0],0x00000F)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED2CONVEND'][0],0x000012)

            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED3LEDSTC'][0],0x00000F)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED3LEDENDC'][0],0x000012)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED3STC'][0],0x000010)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED3ENDC'][0],0x000012)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED3CONVST'][0],0x000014)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED3CONVEND'][0],0x000017)

            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED1LEDSTC'][0],0x000014)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED1LEDENDC'][0],0x000017)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED1STC'][0],0x000015)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED1ENDC'][0],0x000017)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED1CONVST'][0],0x000019)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED1CONVEND'][0],0x00001C)

            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['ALED1STC'][0],0x00001A)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['ALED1ENDC'][0],0x00001C)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['ALED1CONVST'][0],0x00001E)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['ALED1CONVEND'][0],0x000021)

            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['DEEP_SLEEP_STC'][0],0x00002E)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['DEEP_SLEEP_ENDC'][0],0x000038)

            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['DATA_RDY_STC'][0],0x000027)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['DATA_RDY_END'][0],0x000027)

            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED4LEDSTC'][0],0x000019)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['LED4LEDENDC'][0],0x00001C)

            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['DYN_TIA_STC'][0],0x000000)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['DYN_TIA_ENDC'][0],0x000023)

            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['DYN_ADC_STC'][0],0x000000)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['DYN_ADC_ENDC'][0],0x000023)

            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['DYN_CLK_STC'][0],0x000000)
            self.write_register(AFEregisters.TIMING_REGS_250Hz_DICT['DYN_CLK_ENDC'][0],0x000023)


            #self.write_register(AFEregisters.LED1STC,0x000014)
            #self.write_register(AFEregisters.LED1ENDC,0x00001C)

            #self.write_register(AFEregisters.DUAL_PD_REG, 0x000000)
            print("Timing set up done")
        else:
            raise Exception("Invalid timing configuration selected")

    def setSensor(self,sensor):
        if sensor == "SFH7072":
            pass
        elif sensor == "SFH7050":
            pass
        elif sensor == "Custom Board":
            pass
        elif sensor =="OFF":
            pass




        # else:
        #     self.write_register(AFEregisters.PD1STC, 0x000000)
        #     self.write_register(AFEregisters.PD1ENDC, 0x000000)
        #     self.write_register(AFEregisters.PD2STC, 0x000000)
        #     self.write_register(AFEregisters.PD2ENDC, 0x000000)
        #     self.write_register(AFEregisters.DUAL_PD_REG, 0x000000)
        #     #self.set_LED_currents((1,4), (1,4), (1,4), (0,0), 1)
        #     #self.set_BW_early_DAC(0, 1)












if __name__ == '__main__':

    new_board = AFEBoard("/dev/tty.usbmodem14101")
    new_board.set_250Hz_timing("SFH7072")
    new_board.set_LED_currents((1,4.692), (1,4.692), (1,4.692), (0,0), 1)
    new_board.set_BW_early_DAC(0, 1)
    new_board.set_feedback_gains(1, [(3, 0)])
    new_board.set_dc_current_offset(2,[(1, 95, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)])
    x = np.linspace(0,2000,2000)
    print("start")
    vals = new_board.finite_adc_read(2000)

    print("stop")
    new_board.set_LED_currents((1,0),(1,0),(1,0),(1,0),0)
    new_board.close_port()
    plt.plot(x, vals)
    plt.show()








    #new_board.finite_adc_read(50)
