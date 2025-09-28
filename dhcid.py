#!/usr/bin/env python3
import binascii
import hashlib
import sys

def generate_dhcid_from_mac(mac_addr):
    # Convert MAC from colon-separated to raw bytes
    mac_bytes = bytes(int(b, 16) for b in mac_addr.split(":"))

    # Construct the DHCID data: ID type (0) + hardware type (1) + MAC
    data = bytes([0, 1]) + mac_bytes

    # SHA-256 hash as per RFC 4701
    sha256 = hashlib.sha256(data).digest()

    # Base16 (hex) representation, uppercase
    print(binascii.hexlify(sha256).decode("ascii").upper())

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} <MAC address>".format(sys.argv[0]))
        sys.exit(1)

    generate_dhcid_from_mac(sys.argv[1])

