#!/usr/bin/env python3
import argparse
import sys
import re

def parse_timestamp(ts):
    """Parse SRT timestamp to total milliseconds."""
    match = re.match(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})$', ts)
    if not match:
        raise ValueError(f"Invalid timestamp format: {ts}")
    h, m, s, ms = map(int, match.groups())
    return h * 3600000 + m * 60000 + s * 1000 + ms

def format_timestamp(ms):
    """Convert total milliseconds to SRT timestamp."""
    ms = int(round(max(0, ms)))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def parse_offset(offset_str):
    """Parse offset string to milliseconds."""
    try:
        return float(offset_str) * 1000
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid offset value: {offset_str}")

def parse_anchor(anchor_str):
    """Parse anchor string 'T1=T2' to (T1_ms, T2_ms)."""
    if '=' not in anchor_str:
        raise argparse.ArgumentTypeError(f"Anchor must be in format 'T1=T2': {anchor_str}")
    parts = anchor_str.split('=', 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Invalid anchor format: {anchor_str}")
    try:
        t1 = parse_timestamp(parts[0])
        t2 = parse_timestamp(parts[1])
        return (t1, t2)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))

def apply_linear_map(ms, a_src, a_tgt, scale):
    """Apply linear transformation to timestamp."""
    return a_tgt + (ms - a_src) * scale

def process_srt(content, offset_ms=None, anchors=None):
    """Process SRT content with given transformation."""
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.isdigit():
            cue_num = line
            i += 1
            if i >= len(lines):
                raise ValueError("Incomplete subtitle entry")
            time_line = lines[i].strip()
            if '-->' not in time_line:
                raise ValueError(f"Invalid time line: {time_line}")
            times = time_line.split(' --> ')
            if len(times) != 2:
                raise ValueError(f"Invalid time line format: {time_line}")
            start_ms = parse_timestamp(times[0])
            end_ms = parse_timestamp(times[1])
            if offset_ms is not None:
                start_ms = max(0, start_ms + offset_ms)
                end_ms = max(0, end_ms + offset_ms)
            elif anchors:
                (a_src, a_tgt), (b_src, b_tgt) = anchors
                if a_src == b_src:
                    raise ValueError("Source anchor times must be different")
                scale = (b_tgt - a_tgt) / (b_src - a_src)
                start_ms = apply_linear_map(start_ms, a_src, a_tgt, scale)
                end_ms = apply_linear_map(end_ms, a_src, a_tgt, scale)
            result.append(cue_num)
            result.append(f"{format_timestamp(start_ms)} --> {format_timestamp(end_ms)}")
            i += 1
            while i < len(lines) and lines[i].strip():
                result.append(lines[i])
                i += 1
            result.append("")
        else:
            result.append(line)
            i += 1
    return '\n'.join(result)

def main():
    parser = argparse.ArgumentParser(
        description='Shift SRT subtitle timestamps',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('input', help='Input .srt file')
    parser.add_argument('-o', '--output', default='-', help='Output file (default: stdout)')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--offset', type=parse_offset, metavar='SECONDS',
                       help='Offset in seconds (may be negative) to add to all timestamps')
    group.add_argument('--anchor', action='append', metavar='T1=T2',
                       type=parse_anchor, help='Anchor pair (source=target), specify twice')
    args = parser.parse_args()
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied reading '{args.input}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        if args.anchor:
            if len(args.anchor) != 2:
                print("Error: --anchor requires exactly two arguments", file=sys.stderr)
                sys.exit(1)
            anchors = args.anchor
        else:
            anchors = None
        result = process_srt(content, offset_ms=args.offset, anchors=anchors)
    except ValueError as e:
        print(f"Error processing SRT: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
    if args.output == '-':
        print(result)
    else:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
        except PermissionError:
            print(f"Error: Permission denied writing to '{args.output}'", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()
