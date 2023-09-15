# Vis-Partition

### Usage

Given a string in the format:
```
+/- S1[p1a...] S2[p1b...] ... +/- S1[p2a...] S2[p2b...] ... +/- ...
```
where each [pxy...] is a partition, each +/- is either a '+' or '-' and a leading '+' optionally omitted, a visualization in either plain text or LaTeX is produced. The input and/or output can be made to be files.
```
python vis_partition.py [-h] [-i INPUT] [-f FILE] [-o OUT] [-a] [-s SEP] [-t] [-l] [-e] [-c COMMAND] [--no-wrap]
```

### Options
- `-i INPUT`: Read input from commandline
- `-f FILE`, `--file FILE`: Read input from a file (overrides -i)
- `-o OUT`, `--out OUT`: Output to a file (only available with -f)
- `-a`, `--append`: Append to output file rather than overwrite (used with -o)
- `-s SEP`, `--sep SEP`: Separator within in each group (defaults: text=", " latex=",\, ")
- `-t`, `--tall`: When outputting text, print parentheses at full height
- `-l`, `--latex`: Output using LaTeX format
- `-e`, `--environment`: Format LaTeX as an environment (for different packages)
- `-c COMMAND`, `--command COMMAND`: Set the LaTeX command to use (for different packages)
- `--no-wrap`: Disable line wrapping (always used with -o)

- `-h`, `--help`: Show help message and exit

### Input Files
Each line of the file is used as a separate input. In the output, the inputs on separate lines are separated by 4 newlines. Whitespace other than newlines are ignored.

### Examples

- open an interactive session:
  ```
  python vis_partition.py
  ```

- read input from commandline:
  ```
  python vis_partition.py -i "S1[3] S2[1, 1] S3[2, 2] S4[1] - S1[3] S2[0] S3[1, 1] S4[1]"
  ```

- read input from a file:
  ```
  python vis_partition.py -f input.txt
  ```

- output to a file:
  ```
  python vis_partition.py -f input.txt -o output.txt
  ```

- format output as LaTeX:
  ```
  python vis_partition.py -l
  ```

- use a different LaTeX package (e.g. ytableau):
  ```
  python vis_partition.py -l -e -c ytableau
  ```
