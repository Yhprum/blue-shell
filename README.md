# blue-shell
Grand Prix time extracter for Mario Kart: Double Dash!

`getTimeFromRAM.py`

Modify `p1_timer_address` and `p3_timer_address` if needed by running [Dolphin-memory-engine](https://github.com/aldelaro5/Dolphin-memory-engine) and finding the timer location - complete a grand prix race and perform a 4 bytes (word) search for your time converted to ms, repeating until only 1 location is showing (or 2 locations for player 2 for some reason).


`getTimeFromImage.py`

Not fully implemented - a solution to grab grand prix times from a capture card if dolphin can't be used by comparing timer digits to official asset images.
