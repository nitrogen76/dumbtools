# sshfp-record-updater

Simple helper script for updating SSHFP DNS records in FreeIPA using the host's currently installed SSH host keys.

This script:

- Generates SSHFP records from the local host keys using `ssh-keygen`
- Removes existing SSHFP records from the FreeIPA DNS entry
- Replaces them with the current values
- Verifies the resulting DNS record set

Useful for:

- Host rebuilds
- SSH host key rotation
- Automated Puppet/Ansible reconciliation
- Keeping SSHFP records synchronized with reality

---

# Requirements

- FreeIPA client tools (`ipa`)
- Valid Kerberos credentials (`kinit`)
- Permission to modify DNS records in the target zone
- OpenSSH tools (`ssh-keygen`)

---

# Usage

Run locally on a FreeIPA-managed host:

```bash
./sshfp-record-updater.sh
```

Or specify a hostname explicitly:

```bash
./sshfp-record-updater.sh foo.ipa.example.com
```

---

# Example Output

```text
Adding SSHFP: 1 1 b1b3d328b71691a6e8a4d95e73e622d26e071fda
Adding SSHFP: 1 2 c3927ac31b342bc88e2f1ff8f86a23f1c1b08f50788c5d15043391d9aaf5711d
Adding SSHFP: 3 1 fd8d45644c1567d01e5c807a75e83b48874bb1ef
Adding SSHFP: 3 2 e311d6e7da543d14346b4eed37ee16400e1743b3de63feed9eed177fb21cc68b
Adding SSHFP: 4 1 6670769876c5cf6c1a14f7752d946b6168afa11c
Adding SSHFP: 4 2 b9b33ee2f026de9901f8a9535c392f9b6bbb5eef022e1557e4ff35c53b5a0332
```

---

# Verifying Records

Compare DNS output:

```bash
dig +short SSHFP foo.ipa.example.com
```

against:

```bash
ssh-keygen -r foo.ipa.example.com
```

You can also test OpenSSH DNS verification:

```bash
ssh -vvv -o VerifyHostKeyDNS=yes foo.ipa.example.com
```

---

# Notes

- FreeIPA's `dnsrecord-mod` replaces SSHFP values unless all records are supplied in a single invocation.
- This script intentionally updates all SSHFP records at once.
- DNSSEC validation is strongly recommended if using SSHFP for trust verification.

---

