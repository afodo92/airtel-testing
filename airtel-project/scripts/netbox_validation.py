import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import libs.NetBox as NetBox

netbox_session = NetBox.API("demo.netbox.dev", "22afbc69d0e581595c92950e68d3d9239f5118c5")
print(netbox_session.delete_ipam_ip_address_by_id(34))
print(netbox_session.get_ipam_ip_addresses())
#print(netbox_session.create_ipam_ip_address("1.1.1.1","32","active"))
#print(len(netbox_session.get_ipam_ip_addresses()))
