import sys
import os

# -----------------------------
# Parser
# -----------------------------
class Parser:
    def __init__(self, file):
        self.lines = []
        with open(file) as f:
            for line in f:
                line = line.split("//")[0].strip()
                if line:
                    self.lines.append(line)
        self.index = -1
        self.current = None

    def has_more_commands(self):
        return self.index + 1 < len(self.lines)

    def advance(self):
        self.index += 1
        self.current = self.lines[self.index]

    def command_type(self):
        c = self.current.split()[0]
        if c == "push":
            return "C_PUSH"
        if c == "pop":
            return "C_POP"
        if c in ("label",):
            return "C_LABEL"
        if c in ("goto",):
            return "C_GOTO"
        if c in ("if-goto",):
            return "C_IF"
        if c == "function":
            return "C_FUNCTION"
        if c == "call":
            return "C_CALL"
        if c == "return":
            return "C_RETURN"
        return "C_ARITHMETIC"

    def arg1(self):
        if self.command_type() == "C_ARITHMETIC":
            return self.current
        return self.current.split()[1]

    def arg2(self):
        return int(self.current.split()[2])


# -----------------------------
# CodeWriter
# -----------------------------
class CodeWriter:
    def __init__(self, out, bootstrap):
        self.f = open(out, "w")
        self.file_name = ""
        self.label_id = 0
        self.current_function = ""
        if bootstrap:
            self.write_init()

    def set_file_name(self, name):
        self.file_name = name

    def unique(self, prefix):
        self.label_id += 1
        return f"{prefix}.{self.label_id}"

    def write(self, s):
        self.f.write(s + "\n")

    # ---------- Bootstrap ----------
    def write_init(self):
        self.write("@256")
        self.write("D=A")
        self.write("@SP")
        self.write("M=D")
        self.write_call("Sys.init", 0)

    # ---------- Arithmetic ----------
    def write_arithmetic(self, cmd):
        if cmd in ("add", "sub", "and", "or"):
            op = {"add":"+","sub":"-","and":"&","or":"|"}[cmd]
            self.write("@SP")
            self.write("AM=M-1")
            self.write("D=M")
            self.write("A=A-1")
            self.write(f"M=M{op}D")

        elif cmd in ("neg", "not"):
            self.write("@SP")
            self.write("A=M-1")
            self.write("M=" + ("-M" if cmd=="neg" else "!M"))

        elif cmd in ("eq", "gt", "lt"):
            label_true = self.unique("TRUE")
            label_end = self.unique("END")
            jump = {"eq":"JEQ","gt":"JGT","lt":"JLT"}[cmd]
            self.write("@SP")
            self.write("AM=M-1")
            self.write("D=M")
            self.write("A=A-1")
            self.write("D=M-D")
            self.write(f"@{label_true}")
            self.write(f"D;{jump}")
            self.write("@SP")
            self.write("A=M-1")
            self.write("M=0")
            self.write(f"@{label_end}")
            self.write("0;JMP")
            self.write(f"({label_true})")
            self.write("@SP")
            self.write("A=M-1")
            self.write("M=-1")
            self.write(f"({label_end})")

    # ---------- Push / Pop ----------
    def write_push_pop(self, ctype, segment, index):
        if ctype == "C_PUSH":
            if segment == "constant":
                self.write(f"@{index}")
                self.write("D=A")
            elif segment in ("local","argument","this","that"):
                base = {"local":"LCL","argument":"ARG","this":"THIS","that":"THAT"}[segment]
                self.write(f"@{base}")
                self.write("D=M")
                self.write(f"@{index}")
                self.write("A=D+A")
                self.write("D=M")
            elif segment == "temp":
                self.write(f"@{5+index}")
                self.write("D=M")
            elif segment == "pointer":
                self.write("@THIS" if index==0 else "@THAT")
                self.write("D=M")
            elif segment == "static":
                self.write(f"@{self.file_name}.{index}")
                self.write("D=M")
            self.write("@SP")
            self.write("A=M")
            self.write("M=D")
            self.write("@SP")
            self.write("M=M+1")

        else:  # pop
            if segment in ("local","argument","this","that"):
                base = {"local":"LCL","argument":"ARG","this":"THIS","that":"THAT"}[segment]
                self.write(f"@{base}")
                self.write("D=M")
                self.write(f"@{index}")
                self.write("D=D+A")
            elif segment == "temp":
                self.write(f"@{5+index}")
                self.write("D=A")
            elif segment == "pointer":
                self.write("@THIS" if index==0 else "@THAT")
                self.write("D=A")
            elif segment == "static":
                self.write(f"@{self.file_name}.{index}")
                self.write("D=A")
            self.write("@R13")
            self.write("M=D")
            self.write("@SP")
            self.write("AM=M-1")
            self.write("D=M")
            self.write("@R13")
            self.write("A=M")
            self.write("M=D")

    # ---------- Branching ----------
    def write_label(self, label):
        self.write(f"({self.current_function}${label})")

    def write_goto(self, label):
        self.write(f"@{self.current_function}${label}")
        self.write("0;JMP")

    def write_if(self, label):
        self.write("@SP")
        self.write("AM=M-1")
        self.write("D=M")
        self.write(f"@{self.current_function}${label}")
        self.write("D;JNE")

    # ---------- Functions ----------
    def write_function(self, name, n_locals):
        self.current_function = name
        self.write(f"({name})")
        for _ in range(n_locals):
            self.write("@0")
            self.write("D=A")
            self.write("@SP")
            self.write("A=M")
            self.write("M=D")
            self.write("@SP")
            self.write("M=M+1")

    def write_call(self, name, n_args):
        ret = self.unique("RET")
        self.write(f"@{ret}")
        self.write("D=A")
        self.write("@SP"); self.write("A=M"); self.write("M=D")
        self.write("@SP"); self.write("M=M+1")

        for seg in ("LCL","ARG","THIS","THAT"):
            self.write(f"@{seg}")
            self.write("D=M")
            self.write("@SP"); self.write("A=M"); self.write("M=D")
            self.write("@SP"); self.write("M=M+1")

        self.write("@SP")
        self.write("D=M")
        self.write(f"@{n_args+5}")
        self.write("D=D-A")
        self.write("@ARG")
        self.write("M=D")

        self.write("@SP")
        self.write("D=M")
        self.write("@LCL")
        self.write("M=D")

        self.write(f"@{name}")
        self.write("0;JMP")
        self.write(f"({ret})")

    def write_return(self):
        self.write("@LCL")
        self.write("D=M")
        self.write("@R13")
        self.write("M=D")

        self.write("@5")
        self.write("A=D-A")
        self.write("D=M")
        self.write("@R14")
        self.write("M=D")

        self.write("@SP")
        self.write("AM=M-1")
        self.write("D=M")
        self.write("@ARG")
        self.write("A=M")
        self.write("M=D")

        self.write("@ARG")
        self.write("D=M+1")
        self.write("@SP")
        self.write("M=D")

        for i, seg in enumerate(("THAT","THIS","ARG","LCL"), start=1):
            self.write("@R13")
            self.write("D=M")
            self.write(f"@{i}")
            self.write("A=D-A")
            self.write("D=M")
            self.write(f"@{seg}")
            self.write("M=D")

        self.write("@R14")
        self.write("A=M")
        self.write("0;JMP")

    def close(self):
        self.f.close()


# -----------------------------
# Main
# -----------------------------
def main():
    path = sys.argv[1]
    vm_files = []

    if os.path.isdir(path):
        for f in os.listdir(path):
            if f.endswith(".vm"):
                vm_files.append(os.path.join(path, f))
        out = os.path.join(path, os.path.basename(path) + ".asm")
        bootstrap = True
    else:
        vm_files = [path]
        out = path.replace(".vm", ".asm")
        bootstrap = False

    cw = CodeWriter(out, bootstrap)

    for vm in vm_files:
        parser = Parser(vm)
        cw.set_file_name(os.path.splitext(os.path.basename(vm))[0])
        while parser.has_more_commands():
            parser.advance()
            t = parser.command_type()
            if t == "C_ARITHMETIC":
                cw.write_arithmetic(parser.arg1())
            elif t in ("C_PUSH","C_POP"):
                cw.write_push_pop(t, parser.arg1(), parser.arg2())
            elif t == "C_LABEL":
                cw.write_label(parser.arg1())
            elif t == "C_GOTO":
                cw.write_goto(parser.arg1())
            elif t == "C_IF":
                cw.write_if(parser.arg1())
            elif t == "C_FUNCTION":
                cw.write_function(parser.arg1(), parser.arg2())
            elif t == "C_CALL":
                cw.write_call(parser.arg1(), parser.arg2())
            elif t == "C_RETURN":
                cw.write_return()

    cw.close()


if __name__ == "__main__":
    main()
