on run argv
    tell application "Stickies" to activate
    tell application "System Events"
        tell process "Stickies"
            tell window 1
                delay 0.5
                keystroke "n" using command down
                keystroke (item 1 of argv)
                keystroke "f" using {command down, option down}
                keystroke "t" using {command down, option down}
            end tell
        end tell
    end tell
end run

