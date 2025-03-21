"""
Parser module for SES files in the pattern nesting application.
"""
import re
import os


def parse_ses_file(ses_file_path):
    """
    Parse a SES file and extract nesting information
    
    Args:
        ses_file_path (str): Path to the SES file
        
    Returns:
        dict: Parsed nesting data containing marker info and pieces, or None on error
    """
    nesting_data = {
        'marker_info': {},
        'pieces': []
    }

    try:
        with open(ses_file_path, 'r', errors='ignore') as f:
            content = f.read()

            # Extract marker information
            # Width
            width_match = re.search(r'MARKER_WIDTH\s+(\d+(\.\d+)?)', content)
            if width_match:
                nesting_data['marker_info']['width'] = float(width_match.group(1))

            # Alternative width (NWIDTH)
            nwidth_match = re.search(r'NWIDTH\s+(\d+(\.\d+)?)', content)
            if nwidth_match and not width_match:
                nesting_data['marker_info']['width'] = float(nwidth_match.group(1))

            # Check for WIDTH tag (used in some formats)
            width2_match = re.search(r'WIDTH:\s+(\d+(\.\d+)?)', content)
            if width2_match and not width_match and not nwidth_match:
                nesting_data['marker_info']['width'] = float(width2_match.group(1))

            # Length
            length_match = re.search(r'MARKER_LENGTH\s+(\d+(\.\d+)?)', content)
            if length_match:
                nesting_data['marker_info']['length'] = float(length_match.group(1))

            # Alternative length (HEIGHT)
            height_match = re.search(r'HEIGHT:\s+(\d+(\.\d+)?)', content)
            if height_match and not length_match:
                nesting_data['marker_info']['length'] = float(height_match.group(1))

            # Efficiency
            efficiency_match = re.search(r'MARKER_EFFICIENCY\s+(\d+(\.\d+)?)', content)
            if efficiency_match:
                nesting_data['marker_info']['efficiency'] = float(efficiency_match.group(1))

            # Alternative efficiency
            eff2_match = re.search(r'EFFICIENCY:\s+(\d+(\.\d+)?)', content)
            if eff2_match and not efficiency_match:
                nesting_data['marker_info']['efficiency'] = float(eff2_match.group(1))

            # Extract piece information - try multiple patterns
            # Standard BEGIN_PIECE format
            piece_pattern = r'BEGIN_PIECE\s+(\d+)(.*?)END_PIECE'
            piece_matches = re.finditer(piece_pattern, content, re.DOTALL)

            for piece_match in piece_matches:
                piece_id = int(piece_match.group(1))
                piece_data = piece_match.group(2)

                # Extract piece position - try various formats
                x, y = 0, 0

                # Format: NLOC (x,y)
                nloc_match = re.search(r'NLOC\s+\((\d+(\.\d+)?),\s*(\d+(\.\d+)?)\)', piece_data)
                if nloc_match:
                    x = float(nloc_match.group(1))
                    y = float(nloc_match.group(3))
                else:
                    # Try alternative format: NLOC X... Y...
                    loc_x_match = re.search(r'NLOC\s+X\s*([+-]?\d+(\.\d+)?)', piece_data)
                    loc_y_match = re.search(r'NLOC\s+Y\s*([+-]?\d+(\.\d+)?)', piece_data)
                    if loc_x_match and loc_y_match:
                        x = float(loc_x_match.group(1))
                        y = float(loc_y_match.group(1))

                # Extract angle
                angle = 0
                angle_match = re.search(r'ANGLE\s+([+-]?\d+(\.\d+)?)', piece_data)
                if angle_match:
                    angle = float(angle_match.group(1))
                else:
                    # Try alternative rotation format
                    rot_match = re.search(r'ROTATION\s+([+-]?\d+(\.\d+)?)', piece_data)
                    if rot_match:
                        angle = float(rot_match.group(1))

                # Extract flip flag
                flip = 0
                flip_match = re.search(r'FLIP_FLAG\s+(\d+)', piece_data)
                if flip_match:
                    flip = int(flip_match.group(1))

                # Alternative flip flags
                horz_flip_match = re.search(r'HORZ_FLIP\s+(\d+)', piece_data)
                vert_flip_match = re.search(r'VERT_FLIP\s+(\d+)', piece_data)

                if horz_flip_match and int(horz_flip_match.group(1)) == 1:
                    flip = 1

                # Handle PIECE_ID and BUNDLE_ID format
                if piece_id is None or piece_id < 0:
                    piece_id_match = re.search(r'PIECE_ID\s+(\d+)', piece_data)
                    if piece_id_match:
                        piece_id = int(piece_id_match.group(1))

                # Check if we were able to extract a valid ID
                if piece_id is None:
                    print(f"Warning: Unable to extract valid ID from piece data: {piece_data[:100]}...")
                    continue

                # Add piece to the data
                nesting_data['pieces'].append({
                    'id': piece_id,
                    'x': x,
                    'y': y,
                    'angle': angle,
                    'flip': flip
                })

        print(f"Parsed SES file with {len(nesting_data['pieces'])} pieces")

        # Ensure we have a valid width and length
        if 'width' not in nesting_data['marker_info'] or nesting_data['marker_info']['width'] <= 0:
            nesting_data['marker_info']['width'] = 150  # Default width

        if 'length' not in nesting_data['marker_info'] or nesting_data['marker_info']['length'] <= 0:
            # Calculate length based on piece positions
            max_y = 0
            for piece in nesting_data['pieces']:
                max_y = max(max_y, piece['y'] + 50)  # Rough estimate
            nesting_data['marker_info']['length'] = max_y + 20

        # Check if we need to adjust the coordinate system
        # Some nesting software may use a different origin point or coordinate direction
        # Look for pieces outside the expected area
        max_x = max([p['x'] for p in nesting_data['pieces']]) if nesting_data['pieces'] else 0
        max_y = max([p['y'] for p in nesting_data['pieces']]) if nesting_data['pieces'] else 0
        min_x = min([p['x'] for p in nesting_data['pieces']]) if nesting_data['pieces'] else 0
        min_y = min([p['y'] for p in nesting_data['pieces']]) if nesting_data['pieces'] else 0

        print(f"Piece coordinate ranges: X: {min_x} to {max_x}, Y: {min_y} to {max_y}")

        return nesting_data
    except Exception as e:
        import traceback
        print(f"Error parsing SES file: {e}")
        traceback.print_exc()
        return None