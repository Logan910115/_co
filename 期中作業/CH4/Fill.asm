// Fill.asm
// Fills the screen with black when a key is pressed,
// clears it (white) when no key is pressed.

(LOOP)
    // Read keyboard
    @KBD
    D=M

    // If key pressed -> BLACK
    @BLACK
    D;JNE

    // Else -> WHITE
    @WHITE
    0;JMP

(BLACK)
    @color
    M=-1
    @DRAW
    0;JMP

(WHITE)
    @color
    M=0
    @DRAW
    0;JMP

(DRAW)
    // i = SCREEN
    @SCREEN
    D=A
    @i
    M=D

(DRAW_LOOP)
    // if i == SCREEN + 8192 goto LOOP
    @i
    D=M
    @24576
    D=D-A
    @LOOP
    D;JEQ

    // RAM[i] = color
    @color
    D=M
    @i
    A=M
    M=D

    // i++
    @i
    M=M+1

    // continue drawing
    @DRAW_LOOP
    0;JMP
