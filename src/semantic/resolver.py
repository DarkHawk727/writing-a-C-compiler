from typing import Dict

from src.frontend.ast_ir import *


# Might have to use the same counter as in the TACKY pass.
class VariableMap:
    def __init__(self) -> None:
        self._map: Dict[Identifier, Identifier] = {}
        self._counter = 0

    def __getitem__(self, key: Identifier) -> Identifier:
        return self._map[key]

    def __setitem__(self, key: Identifier, value: Identifier) -> None:
        self._map[key] = value

    def __contains__(self, key: Identifier | str) -> bool:
        if isinstance(key, str):
            key = Identifier(key)
        return key in self._map


def _make_unique_name(base: Identifier, env: VariableMap) -> str:
    unique_name = f"{base.name}.{env._counter}"
    env._counter += 1
    return unique_name


def _resolve_declaration(decl: Declaration, env: VariableMap) -> Declaration:
    identifier, initializer = decl
    if identifier in env:
        raise SyntaxError(f"Duplicate declaration of variable {identifier}")
    unique_name = _make_unique_name(identifier, env)
    env[identifier] = Identifier(unique_name)
    init = NULL()
    if not isinstance(initializer, NULL):
        init = _resolve_expression(initializer, env)

    return Declaration(identifier=Identifier(unique_name), initializer=init)


def _resolve_statement(stmt: Statement, env: VariableMap) -> Statement:
    match stmt:
        case Return(return_val):
            return Return(_resolve_expression(return_val, env))
        case exp if isinstance(exp, Expression):
            return _resolve_expression(exp, env)
        case NULL():
            return NULL()
        case _:
            raise SyntaxError(f"Unknown statement type: {stmt}")


def _resolve_expression(exp: Expression, env: VariableMap) -> Expression:
    match exp:
        case Assignment(lhs, rhs):
            if not isinstance(lhs, Variable):
                raise SyntaxError(f"Left-hand side of assignment must be a variable, got {lhs}")
            return Assignment(_resolve_expression(lhs, env), _resolve_expression(rhs, env))
        case Variable(identifier):
            if identifier in env:
                return Variable(env[identifier].name)
            else:
                raise SyntaxError(f"Use of undeclared variable {identifier}")
        case _:
            return exp


def resolve_program(prog: Program) -> Program:
    env = VariableMap()
    resolved_declarations = [_resolve_declaration(decl, env) for decl in prog.function_definition.body]
    resolved_statements = [_resolve_statement(stmt, env) for stmt in prog.function_definition.statements]
    return Program(declarations=resolved_declarations, statements=resolved_statements)
