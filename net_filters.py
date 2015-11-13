from netaddr import IPNetwork, IPAddress


def find_ip(*a, **kw):
    facts = a[0]
    network = IPNetwork(a[1])
    try:
        for addr_txt in facts['ansible_all_ipv4_addresses']:
            if IPAddress(addr_txt) in network:
                return addr_txt
    except KeyError:
        pass
    return None


def find_ipnet(*a, **kw):
    facts = a[0]
    network = IPNetwork(a[1])
    try:
        for addr_txt in facts['ansible_all_ipv4_addresses']:
            if IPAddress(addr_txt) in network:
                return addr_txt + "/" + str(network.prefixlen)
    except KeyError:
        pass
    return None


def find_mac(*a, **kw):
    ip = find_ip(*a, **kw)

    facts = a[0]
    try:
        for int_txt in facts['ansible_interfaces']:
            key = 'ansible_' + int_txt.replace('-', '_')
            if key in facts and 'ipv4' in facts[key] and facts[key]['ipv4']['address'] == ip:
                return facts[key]['macaddress'].upper()
    except KeyError:
        pass
    return None


def find_netdev_with_bridge(facts, cidr, bridge, *args, **kwargs):
    network = IPNetwork(cidr)

    # loop thru the interfaces and look for address that matches cidr
    # this will succeed if device with IP is not yet bridged
    for netdev in facts['ansible_interfaces']:
        brname = netdev.replace('-', '_')
        if brname != bridge:
            devinfo = facts['ansible_' + netdev.replace('-', '_')]
            if ('ipv4' in devinfo and 
                IPAddress(devinfo['ipv4']['address']) in network):
                return netdev

    # check for bridged interfaces on bridge name
    ansible_brname = 'ansible_' + bridge.replace('-', '_')
    if ansible_brname in facts:
        devinfo = facts[ansible_brname]
        if 'ipv4_secondaries' in devinfo:
            for idx, net in enumerate(devinfo['ipv4_secondaries']):
                if 'address' in net and IPAddress(net['address']) in network:
                    # get the first interface in the list from the idx we reached
                    return next(reversed(devinfo['interfaces'][:idx]))


# FIXME: this could be more general. Right now, check if br-ex is there
# and has an address, if so, look for an interface w/out an ip, otherwise
# look for the matching one
def find_netdev(*a, **kw):
    facts = a[0]
    network = IPNetwork(a[1])
    
    try:
        if ('br-ex' in facts['ansible_interfaces'] and
            'ipv4' in facts['ansible_br_ex']):

            for netdev in facts['ansible_interfaces']:
                if (netdev[:3] not in ['br-', 'ovs'] and
                    'ipv4' not in facts['ansible_' + netdev.replace('-', '_')]):
                    return netdev
        else:
            for netdev in facts['ansible_interfaces']:
                devinfo = facts['ansible_' + netdev.replace('-', '_')]
                if ('ipv4' in devinfo and
                    IPAddress(devinfo['ipv4']['address']) in network):
                    return netdev
    except KeyError:
        pass

    return None


class FilterModule(object):
    ''' utility filter to filter list of ips and get the one on the right
network '''

    def filters(self):
        return {'find_ip': find_ip,
                'find_ipnet': find_ipnet,
                'find_netdev': find_netdev,
                'find_netdev_with_bridge': find_netdev_with_bridge,
                'find_mac': find_mac
                }
