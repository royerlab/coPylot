"""
@author:edyoshikun

vortran Stradus Laser python wrapper using RS-232 -> COM device.

For more details regarding operation,
refer to the manuals in https://www.vortranlaser.com/

"""
import serial
from copylot import logger
from copylot.hardware.lasers.abstract_laser import AbstractLaser
from serial.tools import list_ports
import time
from typing import Tuple


class VortranLaser(AbstractLaser):
    # TODO: this probably is better if it's a dictionary and make
    GLOBAL_CMD = ['ECHO', 'PROMPT']
    GLOBAL_QUERY = ['?BPT', '?H', '?IL', '?SFV', '?SPV']
    LASER_CMD = ['C', 'DELAY', 'EPC', 'LC', 'LE', 'LP', 'PP', 'PUL']
    LASER_QUERY = [
        '?C',
        '?CC',
        '?CT',
        '?DELAY',
        '?EPC',
        '?FC',
        '?FD',
        '?FP',
        '?FV',
        '?LC',
        '?LCS',
        '?LE',
        '?LH',
        '?LI',
        '?LP',
        '?LPS',
        '?LW',
        '?MAXP',
        '?OBT',
        '?OBTS',
        '?PP',
        '?PUL',
        '?RP',
    ]
    VOLTRAN_CMDS = GLOBAL_CMD + GLOBAL_QUERY + LASER_CMD + LASER_QUERY

    def __init__(self, name, serial_number=None, port=None, baudrate=19200, timeout=1):
        """
        Wrapper for vortran stradus lasers.
        establishes a connection through COM port

        Default paramters taken from documentation
        Parameters
        ----------
        device_id : str
            serial number for the device
        port : serial
            COM port the device is connected
        baudrate : int
           baudrate for serial communication
        timeout : int
            timeout for write/read in seconds
        """
        # Serial Communication
        self.name = name
        self.port: str = port
        self.baudrate: int = baudrate
        self.address = None
        self.timeout: int = timeout

        # Laser Specs
        self.serial_number: str = None
        self.part_number: int = None
        self.wavelength: int = None
        self.laser_shape: str = None
        self._in_serial_num = serial_number

        # Properties
        self._curr_power = None
        self._ctrl_mode = None
        self._delay = None
        self._ext_power_ctrl = None
        self._current_ctrl = None
        self._toggle_emission = None
        self._pulse_power = None
        self._pulse_mode = None
        self._max_power = None
        self._is_connected = False
        self._status = None

        self.connect()

    def connect(self):
        """
        Establish the serial communication with the device in COM port

        Retrieves information about the laser including:
        - serial number
        - part number
        - wavelength
        - maximum power
        - beam shape

        """
        if self.port is None:
            ports = (
                list_ports.comports()
                if self._in_serial_num is not None
                else [laser[0] for laser in VortranLaser.get_lasers()]
            )
        else:
            ports = [self.port]

        # try to connect to each candidate port
        laser_found = False
        for port in ports:
            self.port = port
            try:
                self.address = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.timeout,
                )
                self._identify_laser()
            except RuntimeError:
                logger.debug(
                    f"A runtime error occurred while attempting to connect to port {self.port}"
                )
                self.disconnect()
                continue

            # if we were able to connect to the port,
            # then we accept the connection *unless* the user specified a serial number,
            # in which case we first check that the laser matches it
            if self._in_serial_num is None or self._in_serial_num == self.serial_number:
                logger.info(
                    f"Connected to Vortran laser {self.serial_number} on serial port {self.port}"
                )
                laser_found = True
                break
            else:
                self.disconnect()

        if not laser_found:
            if self._in_serial_num is not None:
                message = f'No laser found for serial number {self.serial_number}'
            else:
                message = f'No laser found on ports {ports}'
            logger.warning(message)

    def disconnect(self):
        """Disconnects the device"""
        if self.is_connected:
            self.address.close()
        self.address = None

    @property
    def is_connected(self):
        """Check if device is connected to COM Port and return True/False"""
        logger.debug(f'{self.port} is open')
        self._is_connected = self.address is not None and self.address.is_open
        return self._is_connected

    def _write_cmd(self, cmd, value=None):
        """
        Writes the commands to the device

        All commands transmitted must terminate with a
        carriage return “\r” or 0x0D to be processed.

        Parameters
        ----------
        cmd : 'str'
            vortran Stadus command
        value : (int,float,str)
            value to be set with command

        Returns
        -------
        a list with the parsed response from the device to the given command
        """
        try:
            if cmd in VortranLaser.VOLTRAN_CMDS:
                if value is not None:
                    cmd_LF = cmd + '=' + str(value) + '\r'
                else:
                    cmd_LF = cmd + '\r'
                logger.debug(
                    f"Write to laser <{self.serial_number}> -> cmd:<{cmd_LF.encode('utf-8')}>"
                )
                self.address.write(cmd_LF.encode('utf-8'))
                msg_out = self._read_cmd(cmd)
                return msg_out
            else:
                raise ValueError(f"Command '{cmd}' not found")
        except Exception as e:
            raise RuntimeError(f"Error sending command: {str(e)}")

    def _read_cmd(self, cmd):
        """
        Reads the data from the serial port and parses the data in response
        to a sent command

        Parameters
        ----------
        cmd : (str)
            the command written
        Returns
        -------
            the decoded and parsed response to the command
        """
        # All replies to commands are in upper case.
        try:
            elapsed_time = 0
            values = None
            start_time = time.perf_counter()
            while elapsed_time < self.timeout:
                msg = self.address.readline().decode()
                elapsed_time = time.perf_counter() - start_time
                if len(msg) > 1:
                    if msg.endswith('\n') or msg.endswith('\r'):
                        if msg[: len(cmd) + 1] == (cmd + '='):
                            values = msg[len(cmd) + 1 : -2].split(', ')
                            logger.debug(f"msg_out > {msg}")
                            break
            logger.debug(f"Parsed values: {values}")
            if values is None:
                values = ['0']
                # TODO: maybe raise warning?
                # raise Warning
            return values
        except RuntimeWarning:
            logger.info("Error: No response from laser")

    def _identify_laser(self):
        """
        Helper function to identify the parameters for the connected laser.
        Updates the laser information
        (i.e serial number, wavelength, part number, max power, and laser shape)
        """
        laser_param = self._write_cmd('?LI')
        self.serial_number = laser_param[0]
        self.part_number = int(laser_param[1][:-2])  # [nm]
        self.wavelength = int(laser_param[2][:-2])  # [mW]
        self._max_power = float(laser_param[3][:-2])
        self.laser_shape = laser_param[4]
        logger.debug(f'Laser param: {laser_param}')

    # TODO: implement table 9.3.4 from  PDF
    @property
    def drive_control_mode(self):
        """
        Laser Drive Control Mode
        Sets Power or Current Control
        (1 = Current Control)
        """
        self._ctrl_mode = self._write_cmd('?C')[0]
        return self._ctrl_mode

    @drive_control_mode.setter
    def control_mode(self, mode):
        """
        Laser Drive Control Mode
        Sets Power or Current Control
        (1 = Current Control)
        (0 = Power Control)

        """
        self._ctrl_mode = self._write_cmd('C', str(mode))[0]

    @property
    def emission_delay(self):
        """
        Toggle 5 Second Laser Emission Delay On and Off
        (1 = On, 0 = Off)
        """
        self._delay = self._write_cmd('?DELAY')[0]
        return self._delay

    @emission_delay.setter
    def emission_delay(self, mode):
        """
        Toggle 5 Second Laser Emission Delay On and Off
        (1 = On, 0 = Off)
        """
        self._delay = self._write_cmd('DELAY', str(mode))[0]

    @property
    def external_power_control(self):
        """
        Enables External Power Control
        (1= External Control)
        """
        self._ext_power_ctrl = self._write_cmd('?EPC')[0]
        return self._ext_power_ctrl

    @external_power_control.setter
    def external_power_control(self, control):
        """
        Enables External Power Control
        (1= External Control, 0 = Off)
        """
        self._ext_power_ctrl = self._write_cmd('EPC', str(control))[0]

    @property
    def current_control_mode(self):
        """
        Laser Current Control (0-Max)
        """
        self._current_ctrl = self._write_cmd('?LC')[0]
        return self._current_ctrl

    @current_control_mode.setter
    def current_control_mode(self, value):
        """
        Laser Current Control (0-Max)
        """
        self._current_ctrl = self._write_cmd('LC', value)[0]

    @property
    def toggle_emission(self):
        """
        Toggles Laser Emission On and Off
        (1 = On, 0 = Off)
        """
        self._toggle_emission = self._write_cmd('?LE')[0]
        return self._toggle_emission

    @toggle_emission.setter
    def toggle_emission(self, value):
        """
        Toggles Laser Emission On and Off
        (1 = On, 0 = Off)
        """

        if isinstance(value, bool):
            value = str(int(value))
        elif isinstance(value, int):
            value = str(value)

        self._toggle_emission = self._write_cmd('LE', value)[0]

    def turn_on(self):
        """
        Alias function that toggles Laser Emission ON
        """
        logger.info('Turning laser: ON')
        self.toggle_emission = 1
        return self._toggle_emission

    def turn_off(self):
        """
        Alias function that toggles Laser Emission Off
        """
        logger.info('Turning laser: OFF')
        self.toggle_emission = 0
        return self._toggle_emission

    @property
    def power(self):
        """
        Sets the laser power
        Requires pulse_mode() to be OFF
        """
        self._curr_power = float(self._write_cmd('?LP')[0])
        return self._curr_power

    @power.setter
    def power(self, power: float):
        """
        Sets the laser power
        Requires pulse_mode() to be OFF
        """
        if self._max_power is None:
            pass
        if power > self._max_power:
            power = self._max_power
            logger.info(f'Maximum power is: {self._max_power}')
        logger.info(f'Setting power: {power}')
        self._curr_power = float(self._write_cmd('LP', power)[0])

    @property
    def pulse_power(self):
        """
        Pulse Power configuration
        Requires pulse_mode() to be ON
        """
        self._pulse_power = float(self._write_cmd('?PP')[0])
        return self._pulse_power

    @pulse_power.setter
    def pulse_power(self, power):
        """
        Pulse Power configuration
        """
        logger.info(f'Setting Power:{power}')
        if power > self._max_power:
            power = self._max_power
            logger.info(f'Maximum power is: {self._max_power}')
        self._pulse_power = float(self._write_cmd('PP', str(power))[0])

    @property
    def pulse_mode(self):
        """
        Toggle Pulse Mode On and Off (1=On)
        """
        self._pulse_mode = self._write_cmd('?PUL')[0]
        return self._pulse_mode

    @pulse_mode.setter
    def pulse_mode(self, mode=0):
        """
        Toggle Pulse Mode On and Off (1=On)
        """
        logger.debug(f'Digital Modulation: {mode}')
        self._pulse_mode = self._write_cmd('PUL', str(mode))[0]

    @property
    def maximum_power(self) -> float:
        """
        Request Maximum Laser Power
        """
        self._max_power = float(self._write_cmd('?MAXP')[0])
        return self._max_power

    def _echo_off(self):
        self._write_cmd('ECHO', 0)
        logger.debug('Echo Off')

    @property
    def status(self) -> Tuple:
        """
        Request the laser's status and return a tuple with the fault code and description

        """
        fault_code = self._write_cmd('?FC')
        fault_description = self._write_cmd('?FD')
        self._status = (int(fault_code[0]), str(fault_description[0]))
        return self._status

    @staticmethod
    def get_lasers():
        com_ports = list_ports.comports()
        lasers = []
        for port in com_ports:
            try:
                laser = VortranLaser(port=port.device)
                if laser.serial_number is not None:
                    lasers.append((laser.port, laser.serial_number))
                    logger.info(f"Found: {laser.port}:{laser.serial_number}")
                    laser.disconnect()
                else:
                    continue
            except (RuntimeWarning, RuntimeError):
                logger.debug(f'No laser found in {port}')

        if len(lasers) == 0:
            logger.info("No lasers found...")
            raise Exception

        return lasers
