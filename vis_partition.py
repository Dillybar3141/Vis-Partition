"""Partition Visualizer
author:        Dylan Roscow
last modified: September 13, 2023
usage:         see --help
"""
import re
from argparse import ArgumentParser, RawTextHelpFormatter
from sys import stdout
from shutil import get_terminal_size

__version__ = "1.0"
PROG_NAME = "python vis_partition.py"
DESCRIPTION = """description:
    Given an encoding in the format:
        +/- S1[p1a...] S2[p1b...] ... +/- S1[p2a...] S2[p2b...] ... +/- ...
    where each [pxy...] is a partition, each +/- is either a '+' or '-' and
    a leading '+' optionally omitted, a visualization in either plain text
    or LaTeX is produced. The input and/or output can be made to be files."""
EPILOG = f"""input files:
    Each line of the file is used as a separate input. In the output, the
    inputs on separate lines are separated by 4 newlines. Whitespace other
    than newlines are ignored.

examples:
    
    open an interactive session:
        {PROG_NAME}

    read input from commandline:
        {PROG_NAME} -i "S1[3] S2[1, 1] S3[2, 2] S4[1] - S1[3] S2[0] S3[1, 1] S4[1]"

    read input from a file:
        {PROG_NAME} -f input.txt

    output to a file:
        {PROG_NAME} -f input.txt -o output.txt

    format output as LaTeX:
        {PROG_NAME} -l

    use a different LaTeX package (e.g. ytableau):
        {PROG_NAME} -l -e -c ytableau"""


def chunks(iterable, n=1):
    """Yield chunks of size n from iterable."""
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def substring_to_group(substring: str) -> list[list[int]]:
    """Parses a substring of the form:
        S1[partition1] S2[partition2] ...
    Into a list of lists:
        [[partition1], [partition2], ...].

    Example:
        S1[3] S2[1, 1] S3[2, 2] S4[1]
        --> [[3], [1,1], [2,2], [1]]
    """
    part_strings = substring.split("S")[1:]
    parts = [
        x.partition("[")[2].strip().removesuffix("]")
    for x in part_strings]
    output = []
    for part in parts:
        output.append([int(x.strip()) for x in part.split(",")])
    return output


def string_to_encoding(data: str) -> list[list[list[int]]]:
    """Parses a string of the form:
        S1[1a] S2[1b] ... + S1[2a] S2[2b] ... - S1[3a] S2[3b] ... + ...
    Into a list of list of lists:
        [[1, [1a], [1b], ...], [1, [2a], [2b], ...], [-1, [3a], [3b], ...], ...]

    Example:
        S1[3] S2[1, 1] S3[2, 2] S4[1] - S1[3] S2[0] S3[1, 1] S4[1]
        --> [["+", [3], [1,1], [2,2], [1]], ["-", [3], [0], [1,1], [1]]
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
        output.append([sign, *encoding])
    return output


def join_lines(line_groups: list[list[str]], max_lines: int, max_width: int = None) -> str:
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

        
def group_to_lines(group: list[list[int]], idx: int, sep: str, boundary: tuple[str,str]) -> list[str]:
    """Convert a group of partitions into a list of lines to be vertically aligned.
    The separator sep is used between partitions. If the index idx is 0, a leading + is omitted.
    The boundary string is a pair of character to print at the beginning and end usually ("(",")") or (" "," ").
    
    Example:
        group = ["+", [3,2,2], [2,1], [1]]
        -->
        ["+ (xxx, xx, x)",
         "   xx   x     ",
         "   xx         "]
    """
    first_line_parts = []
    for partition in group[1:]:
        max_part = max(max(partition), 1)
        if len(partition) == 1 and partition[0] == 0:
            first_line_parts.append("1")
        else:
            first_line_parts.append("x"*partition[0] + " "*(max_part - partition[0]))
    lines = [group[0] + " (" + sep.join(first_line_parts) + ")"]
    for i in range(1,max(len(partition) for partition in group[1:])):
        line = "  " + boundary[0]
        for j, partition in enumerate(group[1:]):
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


def encoding_to_text(encoding: list[list[list[int]]], sep: str, max_width: int, tall: bool) -> str:
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


def partition_to_latex(partition: list[int], command: str, environment: bool) -> str:
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
    

def encoding_to_latex(encoding: list[list[list[int]]], sep: str, command: str, environment: bool) -> str:
    """Convert an encoding to LaTeX code, with the separator sep between partitions.
    See partition_to_latex for the meaning of the other arguments."""
    output = ""
    for group in encoding:
        partition_strings = [
            partition_to_latex(partition, command, environment)
        for partition in group[1:]]
        output += "\n" + group[0] + " \\left(" + sep.join(partition_strings) + "\\right) "
    output = output[1:]
    if output[0] == "+":
        output = output[1:]
    return output.strip()
    

def display_partitions(data, *, sep=None, as_latex=False, latex_command=None,
                       latex_environment=False, output_stream=None, wrapping=False, tall=False):
    
    if output_stream is None:
        output_stream = stdout
    encoding = string_to_encoding(data)

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
        return argparser.parse_args()
    
    args = parse_args()

    latex_command = "tableau"
    if args.command:
        latex_command = args.command.removeprefix("\\")
    kwargs = {
        "as_latex": args.latex,
        "latex_command": latex_command,
        "latex_environment": args.environment,
        "sep": args.sep,
        "tall": args.tall
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
            while (data := input("\n> ")):
                display_partitions(data, **kwargs, wrapping=(not args.no_wrap))
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()