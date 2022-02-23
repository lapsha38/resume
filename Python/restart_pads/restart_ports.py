#!/usr/bin/python3
'''
Script for reboot all pads, if u got questions call a.golubev
'''
import psycopg2
import nmap
import ipaddress
import configparser
import sys
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException


# read configs from settings.ini
config = configparser.ConfigParser()
config.read("config/conf.ini")


class GetNetwork:
    def __init__(self, place_name):
        super(GetNetwork, self).__init__()
        self.place_name = place_name
        self.router_list = self.main()

    def get_network_addr(self, place_name):
        # db creds
        db_ip = config['DB']['db_ip']
        db = config['DB']['db']
        db_user = config['DB']['db_user']
        db_pass = config['DB']['db_pass']
        # connect to db and get dmz network address
        conn = psycopg2.connect(host=db_ip, dbname=db, user=db_user, password=db_pass)
        cursor = conn.cursor()
        cursor.execute('''SELECT dmz FROM some_place WHERE name LIKE '%{}%';'''.format(place_name))
        dmz_network = cursor.fetchone()[0]
        conn.close()
        return dmz_network

    def get_cisco_ip_addrs(self, dmz_network):
        # use nmap go get active cisco devices
        nm = nmap.PortScanner()
        # get dict from nmap command
        router_dict = nm.scan(hosts=dmz_network, arguments='-n -sP -PE')
        # change netmask cuz we don't wanna use all cisco devices from dmz network
        dmz_net_addr = dmz_network.split('/')[0]
        core_sw_netmast = 28
        core_sw_network = '{}/{}'.format(dmz_net_addr, str(core_sw_netmast))
        # list for cisco devices
        access_sw_list = []
        for key in router_dict['scan']:
            if ipaddress.ip_address(key) in ipaddress.ip_network(core_sw_network):
                access_sw_list.append(key)
        # remove core sw from list
        del access_sw_list[0]
        # return list with correct cisco devices
        return access_sw_list

    # fabric pattern
    def main(self):
        self.network_addr = self.get_network_addr(self.place_name)
        self.cisco_ip_list = self.get_cisco_ip_addrs(self.network_addr)
        return self.cisco_ip_list

class RebootPorts:
    def __init__(self, place):
        super(RebootPorts, self).__init__()
        self.core_dmz = place
        # cisco creds
        self.cisco_username = config['CISCO']['username']
        self.cisco_password = config['CISCO']['password']
        self.cisco_router = self.chech_ssh_or_telnet()
        if self.cisco_router is not None:
            self.ssh = ConnectHandler(**self.cisco_router)
            # call fabric
            self.main()

    # we have to check ssh or telnet is valid connection
    def chech_ssh_or_telnet(self):
        port_scanner = nmap.PortScanner()
        open_ports = port_scanner.scan(self.core_dmz, '22-23')
        # check is 22 port open?
        ssh_is_open = open_ports['scan'][self.core_dmz]['tcp'][22]['state']
        # same for 23 port
        telnet_is_open = open_ports['scan'][self.core_dmz]['tcp'][23]['state']
        # ssh connect
        if ssh_is_open == 'open':
            cisco_router = {
                'device_type': 'cisco_ios',
                'host': self.core_dmz,
                'username': self.cisco_username,
                'password': self.cisco_password,
                'secret': 'cisco',
                'port': 22
            }
            return cisco_router

        # telnet connect
        elif telnet_is_open == 'open':
            cisco_router = {
                'device_type': 'cisco_ios_telnet',
                'host': self.core_dmz,
                'username': self.cisco_username,
                'password': self.cisco_password,
                'secret': 'cisco'
            }
            return cisco_router

    def connect_cisco(self):
        self.ssh.enable()
        return 'Connected'

    # create list with ge/1/0/20, ge/1/0/21 values
    def create_port_list(self):
        # get interfaces from cisco
        result = self.ssh.send_command('show int status | include 90')
        # create empty list
        port_list = []
        # append ports to list
        for line in result.splitlines():
            port_list.append(line[0:9].strip())
        return port_list

    # create str with commands for poweroff/poweronn POE
    def create_reboot_str(self, port_list):
        reboot_str = str()
        for port in port_list:
            shutdown_str = 'interface {} \npower inline never\n'.format(port)
            no_shutdown_str = 'power inline auto\n'
            reboot_str += shutdown_str + no_shutdown_str
        return reboot_str

    def restart_interface(self, ports):
        # poweroff poe then poweron poe on interface
        try:
            self.ssh.send_config_set(ports, cmd_verify=False)
            return '{} Restarted'.format(self.core_dmz)
        except Exception as error:
            return error

    def disconnect_cisco(self):
        self.ssh.exit_enable_mode()
        self.ssh.disconnect()
        return 'Disconnected'

    # fabric pattern
    def main(self):
        try:
            self.connect_cisco()
            self.port_list = self.create_port_list()
            self.create_str = self.create_reboot_str(self.port_list)
            print(self.restart_interface(self.create_str))
            self.restart_interface(self.create_str)
            self.disconnect_cisco()
        except Exception as error:
            print(error)

if __name__ == '__main__':
    # get place shortname from input
    # use it like this: python3 restart_ports.py "some place from database"
    place_name = sys.argv[1]
    router_list = GetNetwork(place_name).router_list
    for router in router_list:
        RebootPorts(router)
