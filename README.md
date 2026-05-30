<img src="runcat.gif" width="150" align="left" />

# pi-runcat

Is a running cat🐱 for your `PI` loading bar

(Yet another useless cat here..)

## pi install 
```bash
wget -P ~/.local/share/fonts "https://github.com/greatyingzi/pi-runcat/releases/download/v1.0.0/runcat.ttf"
pi install npm:pi-runcat
fc-cache -f

# MacOS
curl -L -o ~/Library/Fonts/runcat.ttf "https://github.com/greatyingzi/pi-runcat/releases/download/v1.0.0/runcat.ttf"
# Then restart the app that needs the font. 
# If it still does not appear, you can refresh macOS font caches with:
atsutil databases -removeUser

# Check the font in your terminal 
echo "         "
```

## Manual Installation

Font installation

```bash
cp -r runcat.ttf ~/.local/share/fonts
fc-cache -f
```

##  uninstall 
```bash
pi remove npm:pi-runcat

rm -r ~/.local/share/fonts/runcat.ttf
fc-cache -f

# MacOS
rm ~/Library/Fonts/runcat.ttf
# Then restart the app that was using the font.
# If it still appears, refresh macOS font caches with:
atsutil databases -removeUser
```


Inspired by [runcat-text](https://github.com/bzglve/runcat-text)

Security:
[security check](https://github.com/greatyingzi/pi-runcat)
