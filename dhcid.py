#!/usr/bin/env python3
import hashlib
import base64
import binascii
import sys

def generate_dhcid_record(name: str, base64_dhcid: str, ttl: int = 600) -> str:
    return f"{name.rstrip('.')}.\t{ttl} IN DHCID {base64_dhcid}"

def dhcid_from_mac(mac: str, fqdn: str) -> str:
    ident_type = b'\x00'  # MAC-based
    hwtype = b'\x01'      # Ethernet
    hwaddr = binascii.unhexlify(mac.replace(":", "").lower())
    identifier = ident_type + hwtype + hwaddr
    digest = hashlib.sha256(identifier + fqdn.encode('utf-8').lower()).digest()
    return base64.b64encode(identifier + digest).decode()

def dhcid_from_duid(duid_hex: str, fqdn: str) -> str:
    ident_type = b'\x01'  # DUID-based
    duid = binascii.unhexlify(duid_hex.replace(":", "").replace("-", "").lower())
    identifier = ident_type + duid
    digest = hashlib.sha256(identifier + fqdn.encode('utf-8').lower()).digest()
    return base64.b64encode(identifier + digest).decode()

def usage():
    print("Usage:")
    print("  gen_dhcid_rr.py --mac <mac> <fqdn>")
    print("  gen_dhcid_rr.py --duid <duid> <fqdn>")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        usage()

    mode, ident, fqdn = sys.argv[1], sys.argv[2], sys.argv[3]
    if mode == "--mac":
        dhcid = dhcid_from_mac(ident, fqdn)
    elif mode == "--duid":
        dhcid = dhcid_from_duid(ident, fqdn)
    else:
        usage()

    print(generate_dhcid_record(fqdn, dhcid))

