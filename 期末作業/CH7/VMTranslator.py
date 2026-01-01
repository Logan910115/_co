import sys
import os

ARITHMETIC_CMDS = {
    "add", "sub", "neg",
    "eq", "gt", "lt",
    "and", "or", "not"
}

SEGMENT_BASE = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT"
}

class VMTranslator:
    def __init__(self, vm_file):
        self.vm_file = vm_file
        self.asm_file = vm_file.replace(".vm", ".asm")
        self.file_name = os.path.basename(vm_file).replace(".vm", "")
        self.label_counter = 0

    def translate(self):
        with open(self.vm_file) as f:
            lines = f.readlines()

        asm = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            line = line.split("//")[0].strip()
            parts = line.split()

            if parts[0] in ARITHMETIC_CMDS:
                asm.extend(self.write_arithmetic(parts[0]))
            elif parts[0] in {"push", "pop"}:
                asm.extend(self.write_push_pop(parts[0], parts[1], int(parts[2])))

        with open(self.asm_file, "w") as f:
            f.write("\n".join(asm))

    # -------------------------
    # Arithmetic
    # -------------------------
    def write_arithmetic(self, cmd):
        asm = []

        if cmd in {"add", "sub", "and", "or"}:
            asm += [
                "@SP", "AM=M-1", "D=M",
                "@SP", "AM=M-1"
            ]
            if cmd == "add":
                asm.append("M=M+D")
            elif cmd == "sub":
                asm.append("M=M-D")
            elif cmd == "and":
                asm.append("M=M&D")
            elif cmd == "or":
                asm.append("M=M|D")
            asm += ["@SP", "M=M+1"]

        elif cmd in {"neg", "not"}:
            asm += [
                "@SP", "A=M-1"
            ]
            asm.append("M=-M" if cmd == "neg" else "M=!M")

        elif cmd in {"eq", "gt", "lt"}:
            label_true = f"TRUE_{self.label_counter}"
            label_end = f"END_{self.label_counter}"
            self.label_counter += 1

            asm += [
                "@SP", "AM=M-1", "D=M",
                "@SP", "AM=M-1", "D=M-D",
                f"@{label_true}"
            ]

            if cmd == "eq":
                asm.append("D;JEQ")
            elif cmd == "gt":
                asm.append("D;JGT")
            elif cmd == "lt":
                asm.append("D;JLT")

            asm += [
                "@SP", "A=M", "M=0",
                f"@{label_end}", "0;JMP",
                f"({label_true})",
                "@SP", "A=M", "M=-1",
                f"({label_end})",
                "@SP", "M=M+1"
            ]

        return asm

    # -------------------------
    # Push / Pop
    # -------------------------
    def write_push_pop(self, cmd, segment, index):
        asm = []

        if cmd == "push":
            if segment == "constant":
                asm += [
                    f"@{index}", "D=A"
                ]
            elif segment in SEGMENT_BASE:
                base = SEGMENT_BASE[segment]
                asm += [
                    f"@{base}", "D=M",
                    f"@{index}", "A=D+A", "D=M"
                ]
            elif segment == "temp":
                asm += [
                    f"@{5 + index}", "D=M"
                ]
            elif segment == "pointer":
                asm += [
                    "@THIS" if index == 0 else "@THAT",
                    "D=M"
                ]
            elif segment == "static":
                asm += [
                    f"@{self.file_name}.{index}", "D=M"
                ]

            asm += [
                "@SP", "A=M", "M=D",
                "@SP", "M=M+1"
            ]

        elif cmd == "pop":
            if segment in SEGMENT_BASE:
                base = SEGMENT_BASE[segment]
                asm += [
                    f"@{base}", "D=M",
                    f"@{index}", "D=D+A",
                    "@R13", "M=D",
                    "@SP", "AM=M-1", "D=M",
                    "@R13", "A=M", "M=D"
                ]
            elif segment == "temp":
                asm += [
                    "@SP", "AM=M-1", "D=M",
                    f"@{5 + index}", "M=D"
                ]
            elif segment == "pointer":
                asm += [
                    "@SP", "AM=M-1", "D=M",
                    "@THIS" if index == 0 else "@THAT",
                    "M=D"
                ]
            elif segment == "static":
                asm += [
                    "@SP", "AM=M-1", "D=M",
                    f"@{self.file_name}.{index}", "M=D"
                ]

        return asm


if __name__ == "__main__":
    vm_file = sys.argv[1]
    translator = VMTranslator(vm_file)
    translator.translate()
