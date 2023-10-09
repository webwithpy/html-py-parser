from .data.ast import Block, Stmt, Include, Extends, Python, Html, Variable
from .lexer import Lexer
from .parser import DefaultParser
from typing import List
import copy


class RenderBlock:
    def __init__(self, code: str):
        self.code = code


class DefaultRenderer:
    blocks = {}
    code = ''
    spacing = ''

    @classmethod
    def _render_code(cls, program: List[Stmt]) -> str:
        for index, stmt in enumerate(program):
            match stmt.kind:
                case "block":
                    stmt: Block
                    copied_code = copy.deepcopy(cls.code)
                    copied_spacing = copy.deepcopy(cls.spacing)
                    cls.code = cls.spacing = ''

                    cls._render_code(stmt.block_data)

                    block_code = cls.code
                    cls.blocks[stmt.name] = block_code
                    cls.code, cls.spacing = [copied_code, copied_spacing]
                case "extends":
                    stmt: Extends
                    # simply render file and include it into the program
                    cls.__render_at_file_path(file_path=stmt.file_path)
                case "include":
                    stmt: Include
                    cls.__render_at_file_path(file_path=stmt.file_path)
                case 'variable':
                    stmt: Variable | Block
                    # stmt.code is in this case the name of the block.
                    if stmt.code in cls.blocks:
                        lines = cls.blocks[stmt.code].split('\n')
                        print(lines)
                        for line in lines:
                            cls.code += f'{cls.spacing}{line}\n'
                    else:
                        cls.code += f'{cls.spacing}html += str({stmt.code})\n'
                case "python":
                    stmt: Python
                    cls.code += f'{cls.spacing}{stmt.code}\n'
                    if ':' in stmt.code:
                        cls.spacing += '    '
                case "html":
                    stmt: Html
                    stmt.code = stmt.code.replace('"', "'")
                    cls.code += f'{cls.spacing}html += "{stmt.code}"\n'
                case "pass":
                    cls.spacing = cls.spacing[:-4]

        return cls.code
    
    @classmethod
    def render(cls, program: List[Stmt], **kwargs) -> str:
        code = cls._render_code(program=program)
        kwargs['html'] = ''
        kwargs['RenderBlock'] = RenderBlock
        exec(code, {}, kwargs)

        return kwargs['html']

    @classmethod
    def render_pre(cls, rendered_code: str, **kwargs) -> str:
        kwargs['html'] = ''
        exec(rendered_code, {}, kwargs)

        return kwargs['html']

    @classmethod
    def __render_at_file_path(cls, file_path: str) -> None:
        """
        when a file is for example extended we will need to parse that one too.
        the rendered python will be placed where the extends happens
        :param file_path: path of the file
        :return:
        """
        lexer = Lexer()
        tokens = lexer.lex_file(file_path)
        parser = DefaultParser(tokens)

        program = parser.parse()
        DefaultRenderer._render_code(program)
