<img src="runcat.gif" width="150" align="left" />

# pi-runcat

Is a running cat🐱 for your `PI` loading bar

(Yet another useless cat here..)

## pi install 
```bash
wget -P ~/.local/share/fonts "https://github.com/FredySandoval/pi-runcat/raw/refs/heads/main/runcat.ttf"
pi install npm:pi-runcat
fc-cache -f

# MacOS
curl -L -o ~/Library/Fonts/runcat.ttf "https://github.com/FredySandoval/pi-runcat/raw/refs/heads/main/runcat.ttf"
# Then restart the app that needs the font. 
# If it still does not appear, you can refresh macOS font caches with:
atsutil databases -removeUser
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
```


Inspired by [runcat-text](https://github.com/bzglve/runcat-text)
