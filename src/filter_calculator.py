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

def calculate_multiple_masks_filters(selected_ids, unselected_ids, max_filters=1):
    """
    Calculates up to `max_filters` mask/filter pairs to cover `selected_ids`
    while minimizing collisions with `unselected_ids`.
    
    Returns:
       results: List of tuples (mask, filter_val)
       collisions: List of unselected_ids that are wrongly accepted
    """
    if not selected_ids:
        return [], []
        
    selected_ids = sorted(list(set(selected_ids)))
    
    # 1. Start with one cluster per selected ID (perfect filtering)
    clusters = [[sid] for sid in selected_ids]
    
    # Helper to calculate mask/filter for a cluster
    def calc_mf(ids):
        return calculate_mask_filter(ids)
        
    # Helper to count collisions for a cluster
    def count_collisions(cluster_ids):
        m, f = calc_mf(cluster_ids)
        cols = 0
        for uid in unselected_ids:
            if (uid & m) == (f & m):
                cols += 1
        return cols
        
    # 2. Greedy merge loop
    # We want to reduce len(clusters) to <= max_filters
    # But we prioritize strict correctness first (0 collisions)
    # If we are under max_filters, we stop.
    
    while len(clusters) > 1:
        best_merge = None
        min_added_collisions = float('inf')
        
        
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                new_cluster = clusters[i] + clusters[j]
                
                cols = count_collisions(new_cluster)
                
                
                if cols < min_added_collisions:
                    min_added_collisions = cols
                    best_merge = (i, j)
                
                if min_added_collisions == 0:
                    break # Optimal found, take it
            if min_added_collisions == 0:
                break
                
        should_merge = False
        if min_added_collisions == 0:
            should_merge = True
        elif len(clusters) > max_filters:
            should_merge = True
            
        if should_merge and best_merge:
            i, j = best_merge
            new_c = clusters[i] + clusters[j]
            # Remove j first (larger index)
            clusters.pop(j)
            clusters.pop(i)
            clusters.append(new_c)
        else:
            # We are safe to stop
            break
            
    # 3. Calculate final results
    results = []
    final_collisions = set()
    
    for cluster in clusters:
        m, f = calc_mf(cluster)
        results.append((m, f))
        # Collect actual collisions
        for uid in unselected_ids:
            if (uid & m) == (f & m):
                final_collisions.add(uid)
                
    return results, sorted(list(final_collisions))

def format_hex_bin(value, bits=11):
    return f"0x{value:03X} (bin: {value:0{bits}b})"
