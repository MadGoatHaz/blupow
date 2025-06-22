import struct

def _calculate_crc(data: bytes) -> bytes:
    """Calculate the CRC-16 for a byte array."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')

def _bytes_to_int(bs: bytes, offset: int, size: int, signed: bool = False, scale: float = 1.0) -> float:
    """Convert a byte slice to a scaled integer."""
    value = int.from_bytes(bs[offset:offset+size], byteorder='big', signed=signed)
    return value * scale

def _parse_temperature(value: int, unit: str = "c") -> float:
    """
    Parse a temperature value from a device.
    The 7th bit indicates the sign (0 for positive, 1 for negative).
    """
    temp = (value & 0x7f) * (1 if (value >> 7 == 0) else -1)
    if unit == "f":
        return round(((temp * 9/5) + 32), 2)
    return float(temp) 