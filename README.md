<img src="runcat.gif" width="150" align="left" />

# pi-runcat

Is a runcat port for `PI` for your loading bar

(Yet another useless cat here..)

## pi install 
```bash
wget -P ~/.local/share/fonts "https://github.com/FredySandoval/pi-runcat/raw/refs/heads/main/runcat.ttf"
pi install npm:pi-runcat
fc-cache -f
```

## Manual Installation

Font installation

```bash
cp -r runcat.ttf ~/.local/share/fonts
fc-cache -f
```

## font uninstall 
```bash
rm -r ~/.local/share/fonts/runcat.ttf
fc-cache -f
```


Inspired by [runcat-text](https://github.com/bzglve/runcat-text)
