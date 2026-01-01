// Mult.asm
// Computes R0 * R1 and stores the result in R2.
// Assumes R0 >= 0, R1 >= 0, and R0*R1 < 32768

    // R2 = 0
    @R2
    M=0

    // counter = R1
    @R1
    D=M
    @counter
    M=D

(LOOP)
    // if counter == 0 goto END
    @counter
    D=M
    @END
    D;JEQ

    // R2 = R2 + R0
    @R0
    D=M
    @R2
    M=M+D

    // counter--
    @counter
    M=M-1

    // goto LOOP
    @LOOP
    0;JMP

(END)
    // infinite loop (end program)
    @END
    0;JMP
