# Copyright (c) 2022-2026 José Manuel Barroso Galindo <theypsilon@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# You can download the latest version of this tool from:
# https://github.com/theypsilon/Update_All_MiSTer


# QR Code generator (Version 1-4, Error Correction L, Byte mode)
# Based on ISO/IEC 18004 standard

FORMAT_INFO_0 = 0x77C4  # ECC Level L, Mask 0

# Version info and capacities (data codewords for ECC L)
VERSION_CAPACITIES = {1: 19, 2: 34, 3: 55, 4: 80}
VERSION_SIZES = {1: 21, 2: 25, 3: 29, 4: 33}

# Reed-Solomon generator polynomials (for ECC L)
RS_BLOCKS = {1: (1, 19, 7), 2: (1, 34, 10), 3: (1, 55, 15), 4: (1, 80, 20)}

def _init_gf_tables():
    exp, log = [1] * 512, [0] * 256
    x = 1
    for i in range(255):
        exp[i], log[x] = x, i
        x = (x << 1) ^ 0x11D if x & 0x80 else x << 1
    for i in range(255, 512):
        exp[i] = exp[i - 255]
    return exp, log

GF_EXP, GF_LOG = _init_gf_tables()


def gf_mul(a, b):
    if a == 0 or b == 0:
        return 0
    return GF_EXP[GF_LOG[a] + GF_LOG[b]]


def rs_generator(n):
    g = [1]
    for i in range(n):
        ng = [0] * (len(g) + 1)
        for j, coef in enumerate(g):
            ng[j] ^= coef
            ng[j + 1] ^= gf_mul(coef, GF_EXP[i])
        g = ng
    return g


def rs_encode(data, n_ecc):
    gen = rs_generator(n_ecc)
    msg = data + [0] * n_ecc
    for i in range(len(data)):
        coef = msg[i]
        if coef != 0:
            for j, g in enumerate(gen):
                msg[i + j] ^= gf_mul(g, coef)
    return msg[len(data):]


def encode_data(text):
    bits = "0100"  # Mode indicator for byte
    bits += f"{len(text):08b}"  # Character count (8 bits for version 1-9)
    for c in text.encode("utf-8"):
        bits += f"{c:08b}"
    return bits


def select_version(data_bits):
    for v in range(1, 5):
        capacity = VERSION_CAPACITIES[v] * 8
        if len(data_bits) + 4 <= capacity:  # +4 for terminator
            return v
    raise ValueError("Data too long for QR version 1-4")


def pad_data(bits, version):
    capacity = VERSION_CAPACITIES[version] * 8
    bits += "0000"[:min(4, capacity - len(bits))]  # Terminator
    while len(bits) % 8:
        bits += "0"
    pads = ["11101100", "00010001"]
    i = 0
    while len(bits) < capacity:
        bits += pads[i % 2]
        i += 1
    return bits


def bits_to_bytes(bits):
    return [int(bits[i : i + 8], 2) for i in range(0, len(bits), 8)]


def create_matrix(version):
    size = VERSION_SIZES[version]
    matrix = [[None] * size for _ in range(size)]
    reserved = [[False] * size for _ in range(size)]

    def set_pattern(r, c, pattern):
        for dr, row in enumerate(pattern):
            for dc, val in enumerate(row):
                if 0 <= r + dr < size and 0 <= c + dc < size:
                    matrix[r + dr][c + dc] = val
                    reserved[r + dr][c + dc] = True

    # Finder patterns
    finder = [
        [1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1],
    ]
    set_pattern(0, 0, finder)
    set_pattern(0, size - 7, finder)
    set_pattern(size - 7, 0, finder)

    # Separators
    for i in range(8):
        for r, c in [(7, i), (i, 7), (7, size - 8 + i), (i, size - 8),
                     (size - 8, i), (size - 8 + i, 7)]:
            if 0 <= r < size and 0 <= c < size:
                matrix[r][c] = 0
                reserved[r][c] = True

    # Timing patterns
    for i in range(8, size - 8):
        matrix[6][i] = (i + 1) % 2
        matrix[i][6] = (i + 1) % 2
        reserved[6][i] = True
        reserved[i][6] = True

    # Alignment patterns (version 2+)
    alignment_positions = {2: [18], 3: [22], 4: [26]}
    if version in alignment_positions:
        alignment = [
            [1, 1, 1, 1, 1],
            [1, 0, 0, 0, 1],
            [1, 0, 1, 0, 1],
            [1, 0, 0, 0, 1],
            [1, 1, 1, 1, 1],
        ]
        pos = alignment_positions[version][0]
        # Only place if not overlapping with finder patterns
        if pos > 8:
            set_pattern(pos - 2, pos - 2, alignment)

    # Dark module
    matrix[size - 8][8] = 1
    reserved[size - 8][8] = True

    # Reserve format info areas
    for i in range(9):
        reserved[8][i] = True
        reserved[i][8] = True
    for i in range(8):
        reserved[8][size - 1 - i] = True
    for i in range(7):
        reserved[size - 1 - i][8] = True

    return matrix, reserved


def place_data(matrix, reserved, data_bytes, ecc_bytes):
    size = len(matrix)
    data = data_bytes + ecc_bytes
    bits = "".join(f"{b:08b}" for b in data)
    bit_idx = 0

    col = size - 1
    going_up = True

    while col >= 0:
        if col == 6:
            col -= 1
            continue

        for row in range(size - 1, -1, -1) if going_up else range(size):
            for dc in [0, -1]:
                c = col + dc
                if c >= 0 and not reserved[row][c]:
                    if bit_idx < len(bits):
                        matrix[row][c] = int(bits[bit_idx])
                        bit_idx += 1
                    else:
                        matrix[row][c] = 0

        col -= 2
        going_up = not going_up


def apply_mask(matrix, reserved):
    size = len(matrix)
    for r in range(size):
        for c in range(size):
            if not reserved[r][c] and (r + c) % 2 == 0:  # Mask 0
                matrix[r][c] ^= 1


def add_format_info(matrix):
    size, bits = len(matrix), f"{FORMAT_INFO_0:015b}"
    for i in range(6):
        matrix[8][i] = int(bits[i])
    matrix[8][7], matrix[8][8], matrix[7][8] = int(bits[6]), int(bits[7]), int(bits[8])
    for i in range(6):
        matrix[5 - i][8] = int(bits[9 + i])
    for i in range(8):
        matrix[8][size - 8 + i] = int(bits[7 + i])
    for i in range(7):
        matrix[size - 1 - i][8] = int(bits[i])


def generate_qr(text):
    bits = encode_data(text)
    version = select_version(bits)
    bits = pad_data(bits, version)
    data_bytes = bits_to_bytes(bits)
    ecc_bytes = rs_encode(data_bytes, RS_BLOCKS[version][2])
    matrix, reserved = create_matrix(version)
    place_data(matrix, reserved, data_bytes, ecc_bytes)
    apply_mask(matrix, reserved)
    add_format_info(matrix)
    return matrix


def generate_qr_lines(url: str) -> list[str]:
    matrix = generate_qr(url)
    size = len(matrix)
    lines = []

    # Add 4-module quiet zone, use half-blocks for square aspect ratio
    # ▀ = upper half, ▄ = lower half, █ = full, ' ' = empty
    # Combine 2 rows into 1 line using half-blocks
    # QR: 1=dark=black, 0=light=white
    # Terminal: we want dark modules, so invert for light background appearance

    padded = [[0] * (size + 8) for _ in range(size + 8)]
    for r in range(size):
        for c in range(size):
            padded[r + 4][c + 4] = matrix[r][c]

    height = len(padded)
    for r in range(0, height, 2):
        line = ""
        for c in range(len(padded[0])):
            top = padded[r][c] if r < height else 0
            bot = padded[r + 1][c] if r + 1 < height else 0
            # Invert: 1 (dark module) -> black, 0 (light) -> white
            # Use: █=both dark, ▀=top dark, ▄=bottom dark, ' '=both light
            if top and bot:
                line += "█"
            elif top and not bot:
                line += "▀"
            elif not top and bot:
                line += "▄"
            else:
                line += " "
        lines.append(line)
    return lines
