#!/bin/bash
setxkbmap -option shift:both_capslock
xmodmap ~/.xmodmap
#setxkbmap -option caps:escape
#xmodmap -e "keycode 66 = Escape NoSymbol Escape"
xcape -e 'Mode_switch=Escape'
