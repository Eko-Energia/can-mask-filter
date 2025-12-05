def calculate_mask_filter(selected_ids):
    """
    Calculates the mask and filter for a list of 11-bit CAN IDs.
    Returns a tuple (mask, filter_val).
    """
    if not selected_ids:
        return 0, 0

    # Initialize mask to all 1s (11 bits)
    mask = 0x7FF
    # Initialize filter to the first ID (will be adjusted)
    filter_val = selected_ids[0]

    for can_id in selected_ids[1:]:
        # XOR finds bits that are different
        diff = filter_val ^ can_id
        # If a bit is different, it must be 0 in the mask
        mask &= ~diff
        # The filter value for those bits doesn't matter, but usually we keep them 0 or matching one
        # To be consistent, we can enforce filter bits to be 0 where mask is 0
        # But standard is: filter & mask == id & mask
        
    # Clean up filter: clear bits where mask is 0
    filter_val &= mask

    return mask, filter_val

def format_hex_bin(value, bits=11):
    return f"0x{value:03X} (bin: {value:0{bits}b})"
