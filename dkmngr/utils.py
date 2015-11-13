def get_pretty_lines(lines, nlines=8):
    nlines = max(5, nlines)
    if len(lines) <= nlines:
        return lines
    result = []
    for i in range(nlines / 2):
        result.append(lines[i])
    result.append('... ...')
    for i in range(nlines / 2):
        result.append(lines[len(lines) - nlines / 2 + i])
    return result

