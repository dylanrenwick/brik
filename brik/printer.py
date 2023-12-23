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

    def append(self, msg: str = ''):
        lines = msg.split('\n')
        if len(lines) == 0: return
        indented_lines = [f'{self.get_indent()}{line}' for line in lines if len(line.strip()) > 0]
        if len(indented_lines) > 0 and len(self.content) > 0 and self.content[-1] != '\n':
            indented_lines[0] = lines[0]
        if msg[-1] == '\n':
            if len(indented_lines) > 0:
                indented_lines[-1] += '\n'
            else:
                indented_lines.append('\n')
        new_content = '\n'.join(indented_lines)
        self.content += new_content

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
    
