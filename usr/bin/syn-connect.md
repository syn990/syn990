<a href="https://github.com/syn990"><img src="../../var/chrome/usr-bin-syn-connect.svg" width="100%" alt="foot terminal running man syn-connect. Click the title bar to go back to the desktop."></a>

[◂ Desktop](https://github.com/syn990) · [/usr/bin](./) · syn-connect

```text
SYN-CONNECT(1)               SYN-OS Manual                SYN-CONNECT(1)

NAME
       syn-connect - Wi-Fi, Bluetooth, Ethernet and VPN in one picker

SYNOPSIS
       syn-connect

DESCRIPTION
       One full-screen terminal tool for Wi-Fi, Bluetooth, Ethernet and
       VPN, not four separate popups. It talks to iwd and BlueZ directly
       over D-Bus, with no iwctl or bluetoothctl underneath. Click the
       network icon on the bar to open it. It's a plain terminal
       program, so the same picker runs on the very first boot, before
       anything is installed.

       Wi-Fi lists every network in range with its security type and
       its signal as a bar count, and marks the one you're on. A new
       network that needs a password asks for it right there, masked;
       get it wrong and it lets you try again. A network you've joined
       once before doesn't ask again.

       Bluetooth scans for nearby devices. Enter on a new device pairs,
       trusts and connects it in one step; a paired one just connects.
       Ethernet is read-only: link state, IP address and MAC address,
       straight from the kernel.

       VPN lists the OpenVPN configs in ~/.ovpn/. A config that needs a
       username and password collects them once, through
       syn-uplink-dialpad, and saves them alongside the config. The
       connect step needs root, so doas asks for its password in the
       same window.

KEYS
       Tab, Shift+Tab
              Switch between tabs.
       Up, Down, j, k
              Move the selection.
       Enter  Connect, or pair and connect on Bluetooth.
       d      Disconnect.
       x      Forget a Bluetooth device: unpair and untrust it.
       r      Rescan, or refresh the Ethernet status.
       Esc, q Quit.

FILES
       ~/.ovpn/*.ovpn
              The configs the VPN tab lists.

SEE ALSO
       syn-uplink-dialpad(1), syn-bar-core(1), syn-audio(1), iwd(8),
       bluetoothctl(1), openvpn(8), doas(1)

SYN-OS                            2026                    SYN-CONNECT(1)
```

Full documentation: [syn-connect.md](https://github.com/syn990/SYN-OS/blob/main/SYN-ISO-PROFILE/airootfs/usr/share/syn-os/docs/tools/syn-connect.md) · Source: [SYN-SOFTWARE/syn-connect-src](https://github.com/syn990/SYN-OS/tree/main/SYN-SOFTWARE/syn-connect-src)
