import sys
import os

# -----------------------------
# Hack Assembler (Project 6)
# -----------------------------

# Predefined symbols
PREDEFINED_SYMBOLS = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    "SCREEN": 16384,
    "KBD": 24576,
}

for i in range(16):
    PREDEFINED_SYMBOLS[f"R{i}"] = i


# C-instruction tables
DEST_TABLE = {
    None:   "000",
    "M":    "001",
    "D":    "010",
    "MD":   "011",
    "DM":   "011",
    "A":    "100",
    "AM":   "101",
    "MA":   "101",
    "AD":   "110",
    "DA":   "110",
    "AMD":  "111",
    "ADM":  "111",
    "MAD":  "111",
    "MDA":  "111",
    "DAM":  "111",
    "DMA":  "111",
}

COMP_TABLE = {
    "0":   "0101010",
    "1":   "0111111",
    "-1":  "0111010",
    "D":   "0001100",
    "A":   "0110000",
    "M":   "1110000",
    "!D":  "0001101",
    "!A":  "0110001",
    "!M":  "1110001",
    "-D":  "0001111",
    "-A":  "0110011",
    "-M":  "1110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "M+1": "1110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "M-1": "1110010",
    "D+A": "0000010",
    "D+M": "1000010",
    "D-A": "0010011",
    "D-M": "1010011",
    "A-D": "0000111",
    "M-D": "1000111",
    "D&A": "0000000",
    "D&M": "1000000",
    "D|A": "0010101",
    "D|M": "1010101",
}

JUMP_TABLE = {
    None:  "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}


def clean_line(line):
    line = line.split("//")[0]
    return line.strip()


def first_pass(lines, symbol_table):
    rom_address = 0
    for line in lines:
        line = clean_line(line)
        if not line:
            continue
        if line.startswith("(") and line.endswith(")"):
            label = line[1:-1]
            symbol_table[label] = rom_address
        else:
            rom_address += 1


def second_pass(lines, symbol_table):
    result = []
    next_ram_address = 16

    for line in lines:
        line = clean_line(line)
        if not line or (line.startswith("(") and line.endswith(")")):
            continue

        # A-instruction
        if line.startswith("@"):
            symbol = line[1:]
            if symbol.isdigit():
                address = int(symbol)
            else:
                if symbol not in symbol_table:
                    symbol_table[symbol] = next_ram_address
                    next_ram_address += 1
                address = symbol_table[symbol]

            binary = "0" + format(address, "015b")
            result.append(binary)
            continue

        # C-instruction
        dest, comp, jump = None, None, None

        if "=" in line:
            dest, rest = line.split("=")
        else:
            rest = line

        if ";" in rest:
            comp, jump = rest.split(";")
        else:
            comp = rest

        binary = (
            "111"
            + COMP_TABLE[comp]
            + DEST_TABLE[dest]
            + JUMP_TABLE[jump]
        )
        result.append(binary)

    return result


def assemble(input_path):
    with open(input_path, "r") as f:
        lines = f.readlines()

    symbol_table = dict(PREDEFINED_SYMBOLS)

    first_pass(lines, symbol_table)
    machine_code = second_pass(lines, symbol_table)

    output_path = input_path.replace(".asm", ".hack")
    with open(output_path, "w") as f:
        for line in machine_code:
            f.write(line + "\n")

    print(f"✔ Assembled: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].endswith(".asm"):
        print("Usage: python assembler.py Prog.asm")
        sys.exit(1)

    assemble(sys.argv[1])
