"""Partition Visualizer
author:        Dylan Roscow
last modified: September 13, 2023
usage:         see --help
"""
import re
from argparse import ArgumentParser, RawTextHelpFormatter
from sys import stdout
from shutil import get_terminal_size

__version__ = "1.1"
PROG_NAME = "python vis_partition.py"
DESCRIPTION = """description:
    Given an encoding in the format:
        +/- c1S1[p1a...] S2[p1b...] ... +/- c2S1[p2a...] S2[p2b...] ... +/- ...
    where each [pxy...] is a partition, each +/- is either a '+' or '-',
    each cx is an integer coefficient and a leading '+' or coefficient is
    optionally omitted, a visualization in either plain text or LaTeX is
    produced. The partitions are sorted based the index on S, so both of
    S1[p1]S2[p2] and S2[p2]S1[p1] produce the same result. Additionally,
    The input and/or output can be made to be files. Outputs are automatically
    line-wrapped to fit your terminal size, so if you resize the terminal,
    the partitions may not display correctly."""
EPILOG = """input files:
    Each line of the file is used as a separate input. In the output, the
    inputs on separate lines are separated by 4 newlines. Whitespace other
    than newlines are ignored.

examples:
    
    open an interactive session:
        python vis_partition.py

    read input from commandline:
        python vis_partition.py -i "S1[3] S2[1, 1] S3[2, 2] S4[1] - S1[3] S2[0] S3[1, 1] S4[1]"

    read input from a file:
        python vis_partition.py -f input.txt

    output to a file:
        python vis_partition.py -f input.txt -o output.txt

    format output as LaTeX:
        python vis_partition.py -l

    use a different LaTeX package (e.g. ytableau):
        python vis_partition.py -l -e -c ytableau"""


def chunks(iterable, n=1):
    """Yield chunks of size n from iterable."""
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def removeprefix(s, prefix):
    if s.startswith(prefix):
        return s[len(prefix):]
    return s


def removesuffix(s, suffix):
    if s.endswith(suffix):
        return s[:-len(suffix)]
    return s


def substring_to_group(substring):
    """Parses a substring of the form:
        aS1[partition1...] S2[partition2...] ...
    Into a list of lists:
        ["a", ["S1", partition1...], ["S2", partition2...], ...].

    Example:
        2S1[3] S2[1, 1] S4[2, 2] S3[1]
        --> ["a", ["S1", 3], ["S2", 1,1], ["S4", 2,2], ["S3", 1]]
    """
    lead, substring, _ = re.split(r"(S.*)", substring, maxsplit=1)
    s_part_strings = re.split(r"(S\d+)", substring)[1:]
    s_strings = s_part_strings[::2]
    part_strings = s_part_strings[1::2]
    s_ints = [int(removeprefix(x, "S")) for x in s_strings]
    parts = [
        removesuffix(removeprefix(x.strip(), "["), "]")
    for x in part_strings]
    terms = list(zip(s_ints, parts))
    terms.sort(key = lambda x: x[0])
    output = [lead]
    for _, part in terms:
        output.append([int(x.strip()) for x in part.split(",")])
    return output


def string_to_encoding(data):
    """Parses a string of the form:
        aS1[1a] S2[1b] ... + bS1[2a] S2[2b] ... - cS1[3a] S2[3b] ... + ...
    Into a list of list of lists:
        [["+", "a", ["S1", 1a], ["S2", 1b], ...], ["+", "b", ["S1", 2a], ["S2", 2b], ...], ["-", "c", ["S1", 3a], ["S2", 3b], ...], ...]

    Example:
        S1[3] S2[1, 1] S3[2, 2] S4[1] - 3S1[3] S2[0] S3[1, 1] S4[1]
        --> [["+", ["S1", 3], ["S2", 1, 1], ["S3", 2,2], ["S4", 1]], ["-", "3", ["S1", 3], ["S2", 0], ["S3", 1, 1], ["S4", 1]]
    """
    substrings = re.split(r"(\+|-)", data)
    substrings = [x.strip() for x in substrings]
    if len(substrings[0]) == 0:
        substrings = substrings[1:]
    else:
        substrings.insert(0, "+")
    assert len(substrings) % 2 == 0
    output = []
    for sign, substring in chunks(substrings, 2):
        encoding = substring_to_group(substring)
        output.append([sign] + encoding)
    return output


def join_lines(line_groups, max_lines, max_width=None):
    """Join groups of lines in parallel rows such that no row exceeds max_width.
    
    Example:
        line_groups = [["aaa ", "aa  ", "a "], ["bb ", "b  ", "   "], ["c", "c", " "]]
        -->
        "aaa bb c
         aa  b  c
         a       "
    """
    idx = 0
    chunk_strings = []
    adjusted_width = int(max_width * 0.9)
    while idx < len(line_groups):
        chunk = [line_groups[idx]]
        idx += 1
        while idx < len(line_groups) and sum(len(c[0]) for c in chunk) + len(line_groups[idx][0]) < adjusted_width:
            chunk.append(line_groups[idx])
            idx += 1
        chunk_strings.append("\n".join([
            " ".join([lines[i] for lines in chunk])
        for i in range(max_lines)]))
    return "\n\n".join(chunk_strings)

        
def group_to_lines(group, idx, sep, boundary):
    """Convert a group of partitions into a list of lines to be vertically aligned.
    The separator sep is used between partitions. If the index idx is 0, a leading + is omitted.
    The boundary string is a pair of character to print at the beginning and end usually ("(",")") or (" "," ").
    
    Example:
        group = ["+", "2", [3,2,2], [2,1], [1]]
        -->
        ["+ 2(xxx, xx, x)",
         "    xx   x     ",
         "    xx         "]
    """
    first_line_parts = []
    for partition in group[2:]:
        max_part = max(max(partition), 1)
        if len(partition) == 1 and partition[0] == 0:
            first_line_parts.append("1")
        else:
            first_line_parts.append("x"*partition[0] + " "*(max_part - partition[0]))
    lines = [group[0] + " " + group[1] + "(" + sep.join(first_line_parts) + ")"]
    for i in range(1,max(len(partition) for partition in group[2:])):
        line = "  " + " "*len(group[1]) + boundary[0]
        for j, partition in enumerate(group[2:]):
            max_part = max(max(partition), 1)
            spacing = " "*len(sep) if j > 0 else ""
            part = partition[i] if i < len(partition) else 0
            line += spacing + "x"*part + " "*(max_part - part)
        line += boundary[1]
        lines.append(line)
    if idx == 0 and group[0] == "+":
        lines = [line[2:] for line in lines]
    assert all(len(line) == len(lines[0]) for line in lines)
    return lines


def encoding_to_text(encoding, sep, max_width, tall):
    """Convert an encoding to plain text, with the seperator sep between partitions.
    If max_width is specified, lines will wrap such that no line exceeds the max_width.
    If tall is true, the parentheses will extend the full height.
    """
    boundary = ("(", ")") if tall else (" ", " ")
    line_groups = [group_to_lines(group, i, sep, boundary) for i, group in enumerate(encoding)]
    max_lines = max(len(lines) for lines in line_groups)
    for lines in line_groups:
        lines += [" "*len(lines[0])]*(max_lines - len(lines))
    if max_width is None:
        final_lines = [
            " ".join([lines[i] for lines in line_groups])
        for i in range(max_lines)]
        return "\n".join(final_lines)
    else:
        return join_lines(line_groups, max_lines, max_width)


def partition_to_latex(partition, command, environment):
    """Generate the LaTeX code for a single partition. Use the specified latex command.
    If latex_environment is set, it will generate code for an environment rather than a command.
    
    Example:
        [3, 2, 2, 1]
        --> \\command{~ & ~ & ~ \\\\ ~ & ~ \\\\ ~ & ~ \\\\ ~}
     or --> \\begin{command} ~ & ~ & ~ \\\\ ~ & ~ \\\\ ~ & ~ \\\\ ~ \\end{command}
    """
    if len(partition) == 1 and partition[0] == 0:
        return "1"
    compact_partition = [p for p in partition if p > 0]
    parts = [" & ".join(["~"]*p) for p in compact_partition]
    if environment:
        return "\\begin{" + command + "} " + " \\\\ ".join(parts) + "\\end{" + command + "}"
    else:
        return "\\" + command + "{" + " \\\\ ".join(parts) + "}"
    

def encoding_to_latex(encoding, sep, command, environment):
    """Convert an encoding to LaTeX code, with the separator sep between partitions.
    See partition_to_latex for the meaning of the other arguments."""
    output = ""
    for group in encoding:
        partition_strings = [
            partition_to_latex(partition, command, environment)
        for partition in group[2:]]
        output += "\n" + group[0] + " " + group[1] + "\\left(" + sep.join(partition_strings) + "\\right) "
    output = output[1:]
    if output[0] == "+":
        output = output[1:]
    return output.strip()
    

def display_partitions(data, sep=None, as_latex=False, latex_command=None, latex_environment=False, output_stream=None, wrapping=False, tall=False, verbose=False):
    
    if output_stream is None:
        output_stream = stdout
    try:
        encoding = string_to_encoding(data)
    except Exception:
        print("Failed to Decode Input String")
        if verbose:
            raise
        return

    # Check for any invalid groups
    if any(len(group) == 1 for group in encoding):
        empty_groups = [i for i, group in enumerate(encoding) if len(group) == 1]
        group_s, index_s = "groups","indices"
        if len(empty_groups) == 1:
            empty_groups = empty_groups[0]
            group_s, index_s = "group", "index"
        print("Invalid Input: zero length", group_s, "at", index_s, empty_groups, file=output_stream)
        print("(ex: \"S1[3] S2[1, 1] S3[2, 2] S4[1] - S1[3] S2[0] S3[1, 1] S4[1]\")", file=output_stream)
        return
    
    try:

        if output_stream == stdout:
            print("", file=output_stream)

        if as_latex:
            if latex_command is None:
                latex_command = "tableau"
            if sep is None:
                sep = ",\, "
            output = encoding_to_latex(encoding, sep, latex_command, latex_environment)

        else:
            if sep is None:
                sep = ", "
            if wrapping:
                width, _ = get_terminal_size((60, 20))
            else:
                width = None
            output = encoding_to_text(encoding, sep, width, tall)

        print(output, file=output_stream)

    except Exception:
        print("Failed to Display Encoding")
        if verbose:
            raise
        return
    

def main():

    def parse_args():
        argparser = ArgumentParser(prog=PROG_NAME, description=DESCRIPTION, epilog=EPILOG, formatter_class=RawTextHelpFormatter)
        argparser.add_argument("-i", dest="input", action="store", help="Read input from commandline")
        argparser.add_argument("-f", "--file", action="store", help="Read input from a file (overrides -i)")
        argparser.add_argument("-o", "--out", action="store", help="Output to a file (only available with -f)")
        argparser.add_argument("-a", "--append", action="store_true", help="Append to output file rather than overwrite (used with -o)")
        argparser.add_argument("-s", "--sep", action="store", help="Separator within in each group (defaults: text=\", \" latex=\",\\, \")")
        argparser.add_argument("-t", "--tall", action="store_true", help="When outputting text, print parentheses at full height")
        argparser.add_argument("-l", "--latex", action="store_true", help="Output using LaTeX format")
        argparser.add_argument("-e", "--environment", action="store_true", help="Format LaTeX as an environment (for different packages)")
        argparser.add_argument("-c", "--command", action="store", help="Set the LaTeX command to use (for different packages)")
        argparser.add_argument("--no-wrap", action="store_true", help="Disable line wrapping (always used with -o)")
        argparser.add_argument("--verbose", action="store_true", help="Print full error tracebacks")
        return argparser.parse_args()
    
    args = parse_args()

    latex_command = "tableau"
    if args.command:
        latex_command = removeprefix(args.command, "\\")
    kwargs = {
        "as_latex": args.latex,
        "latex_command": latex_command,
        "latex_environment": args.environment,
        "sep": args.sep,
        "tall": args.tall,
        "verbose": args.verbose
    }

    if args.file:
        with open(args.file, "r") as f:
            data = f.read()
        if args.out and not args.append:
            with open(args.out, "w") as f:
                f.write("")
        if args.out:
            with open(args.out, "a") as f:
                for i, d in enumerate(re.split(r"[\n]{2,}", data)):
                    display_partitions(d, **kwargs, wrapping=False, output_stream=f)
                    print("\n\n", file=f)
        else:
            for i, d in enumerate(re.split(r"[\n]{2,}", data)):
                if i > 0: print("\n\n")
                display_partitions(d, **kwargs, wrapping=(not args.no_wrap))
    elif args.input:
        data = args.input
        display_partitions(data, **kwargs, wrapping=(not args.no_wrap))
    else:
        print("Enter input string (Press enter with no input to exit; for other input methods see --help):")
        try:
            data = input("\n> ")
            while data:
                display_partitions(data, **kwargs, wrapping=(not args.no_wrap))
                data = input("\n> ")
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()
