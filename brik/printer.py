import re

class Printer:
    def __init__(self, indent_style='\t'):
        self.clear()
        self.indent_style = indent_style

    def get_indent(self)-> str:
        return self.indent_style * self.indent
    def clear(self):
        self.content = ''
        self.indent = 0

    def right(self):
        self.indent += 1
    def left(self):
        self.indent -= 1

    def _append(self, msg: str):
        if msg == '\n': self.content += msg
        elif Printer._whitespace_regex.match(msg) is not None and (len(self.content) == 0 or self.content[-1] == '\n'):
            return
        elif len(self.content) > 0 and self.content[-1] != '\n': self.content += msg
        else: self.content += f'{self.get_indent()}{msg}'

    _whitespace_regex = re.compile('^[ \t\r\n]*$')
    def append(self, msg: str = ''):
        lines = msg.split('\n')
        line_count = len(lines)
        if line_count == 0: return
        for i in range(0, line_count):
            msg = f'{lines[i]}\n' if i < line_count - 1 else lines[i]
            self._append(msg)

    def append_ln(self, msg: str = ''):
        self.append(f'{msg}\n')

    def print(self, obj):
        if '__pretty_print__' in dir(obj):
            obj.__pretty_print__(self)
        else:
            self.append(str(obj))

    def __str__(self)-> str:
        return self.content
    def __repr__(self)-> str:
        return str(self)
    
