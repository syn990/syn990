<a href="https://github.com/syn990"><img src="../../var/chrome/usr-bin-syn-audio.svg" width="100%" alt="foot terminal running man syn-audio. Click the title bar to go back to the desktop."></a>

[◂ Desktop](https://github.com/syn990) · [/usr/bin](./) · syn-audio

```text
SYN-AUDIO(1)                 SYN-OS Manual                  SYN-AUDIO(1)

NAME
       syn-audio - audio mixer in the terminal, no pavucontrol

SYNOPSIS
       syn-audio
       syn-audio --list-sinks | --list-sources | --list-cards
       syn-audio --set-default-sink | --set-default-source <name>
       syn-audio --mute-sink | --mute-source <name> on|off|toggle
       syn-audio --set-sink-volume | --set-source-volume <name> <0-100>
       syn-audio --adjust-sink-volume | --adjust-source-volume
                 <name> <+-N>
       syn-audio --set-profile <card> <profile>

DESCRIPTION
       SYN-OS doesn't ship the usual audio panel. syn-audio is a small,
       purpose-built mixer that opens straight in the terminal and
       talks to the sound server directly through libpulse, with no
       pactl underneath. Click the volume icon on the bar to open it.

       With no arguments you get your outputs (speakers, headphones)
       and inputs (microphones), each with a volume bar, and your sound
       cards' profiles below them. A dot marks the default device and
       an M marks anything muted. Changes made elsewhere, like
       scrolling on the bar's volume icon, show up straight away.

       Middle-click the volume icon to mute without opening the mixer
       at all. The flags do the same jobs from a script or a menu; the
       --list options print one tab-separated line per device or
       profile.

KEYS
       Tab    Switch between outputs, inputs and profiles.
       Up, Down, j, k
              Move the selection.
       Enter  Make the device the default, or switch to the profile.
       m      Mute or unmute it.
       Left, Right, h, l
              Turn the volume down or up, 5% a step.
       Esc, q Quit.

SEE ALSO
       syn-bar-core(1), syn-connect(1), syn-crypter(1), pipewire(1)

SYN-OS                            2026                      SYN-AUDIO(1)
```

Full documentation: [audio.md](https://github.com/syn990/SYN-OS/blob/main/SYN-ISO-PROFILE/airootfs/usr/share/syn-os/docs/tools/audio.md) · Source: [SYN-SOFTWARE/syn-audio-src](https://github.com/syn990/SYN-OS/tree/main/SYN-SOFTWARE/syn-audio-src)
