"""
Motor de fórmulas seguro para evaluación de expresiones matemáticas.
Soporta: +, -, *, /, (), variables, MIN, MAX, ROUND
"""
import re
from typing import Dict, List, Set, Tuple, Any


class FormulaError(Exception):
    """Error en evaluación de fórmulas"""
    pass


class FormulaParser:
    """Parser seguro de fórmulas matemáticas"""
    
    OPERATORS = {
        '+': (1, lambda a, b: a + b),
        '-': (1, lambda a, b: a - b),
        '*': (2, lambda a, b: a * b),
        '/': (2, lambda a, b: a / b if b != 0 else None),
        '=': (0, lambda a, b: 1 if abs(a - b) < 0.0001 else 0),  # Comparación
        '>': (0, lambda a, b: 1 if a > b else 0),
        '<': (0, lambda a, b: 1 if a < b else 0),
    }
    
    FUNCTIONS = {
        'MIN': lambda *args: min(args) if args else 0,
        'MAX': lambda *args: max(args) if args else 0,
        'ROUND': lambda x, d=0: round(x, int(d)),
        'IF': lambda cond, val_true, val_false: val_true if cond != 0 else val_false,
        'SI': lambda cond, val_true, val_false: val_true if cond != 0 else val_false,  # Alias español
    }

    @staticmethod
    def tokenize(formula: str) -> List[str]:
        """Convierte fórmula en tokens"""
        formula = formula.upper().replace(' ', '')
        # Soportar =, >, <, >=, <=, <>
        formula = formula.replace('>=', '≥').replace('<=', '≤').replace('<>', '≠')
        # Solo ; como separador de argumentos (no coma para evitar ambigüedad con decimales)
        pattern = r'(\d+\.?\d*|[A-Z_][A-Z0-9_]*|[+\-*/()=><≥≤≠]|;)'
        tokens = re.findall(pattern, formula)
        return tokens

    @staticmethod
    def extract_variables(formula: str) -> Set[str]:
        """Extrae variables de una fórmula"""
        tokens = FormulaParser.tokenize(formula)
        variables = set()
        for token in tokens:
            if token and token[0].isalpha() and token not in FormulaParser.FUNCTIONS:
                variables.add(token)
        return variables

    @staticmethod
    def evaluate(formula: str, variables: Dict[str, Any]) -> float:
        """Evalúa una fórmula con variables dadas"""
        if not formula or not formula.strip():
            raise FormulaError("Fórmula vacía")
        
        # Normalizar variables: bool -> 0/1, text -> error, select -> string o número
        normalized_vars = {}
        for key, value in variables.items():
            if isinstance(value, bool):
                normalized_vars[key] = 1 if value else 0
            elif isinstance(value, (int, float)):
                normalized_vars[key] = float(value)
            elif isinstance(value, str):
                # Intentar convertir string a número
                try:
                    normalized_vars[key] = float(value.replace(',', '.'))
                except (ValueError, AttributeError):
                    # Si no es número, dejar como string para comparaciones
                    # Ejemplo: TIPO = "BALCON"
                    normalized_vars[key] = value.upper()
            else:
                normalized_vars[key] = float(value)
        
        tokens = FormulaParser.tokenize(formula)
        return FormulaParser._evaluate_tokens(tokens, normalized_vars)

    @staticmethod
    def _evaluate_tokens(tokens: List[str], variables: Dict[str, float]) -> float:
        """Evalúa tokens usando Shunting Yard + evaluación RPN"""
        output = []
        operators = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # Número
            if token.replace('.', '').isdigit():
                output.append(float(token))
            
            # Variable
            elif token[0].isalpha() and token not in FormulaParser.FUNCTIONS:
                if token not in variables:
                    raise FormulaError(f"Variable '{token}' no definida")
                output.append(variables[token])
            
            # Función
            elif token in FormulaParser.FUNCTIONS:
                operators.append(token)
            
            # Operador
            elif token in FormulaParser.OPERATORS:
                while (operators and 
                       operators[-1] != '(' and 
                       operators[-1] in FormulaParser.OPERATORS and
                       FormulaParser.OPERATORS[operators[-1]][0] >= FormulaParser.OPERATORS[token][0]):
                    FormulaParser._apply_operator(output, operators.pop())
                operators.append(token)
            
            # Paréntesis izquierdo
            elif token == '(':
                operators.append(token)
            
            # Paréntesis derecho o punto y coma
            elif token in (')', ';'):
                while operators and operators[-1] != '(':
                    FormulaParser._apply_operator(output, operators.pop())
                
                if token == ')':
                    if not operators or operators[-1] != '(':
                        raise FormulaError("Paréntesis desbalanceados")
                    operators.pop()
                    
                    # Aplicar función si hay una
                    if operators and operators[-1] in FormulaParser.FUNCTIONS:
                        FormulaParser._apply_function(output, operators.pop())
            
            i += 1
        
        # Aplicar operadores restantes
        while operators:
            op = operators.pop()
            if op == '(':
                raise FormulaError("Paréntesis desbalanceados")
            FormulaParser._apply_operator(output, op)
        
        if len(output) != 1:
            raise FormulaError("Fórmula inválida")
        
        result = output[0]
        if result is None:
            raise FormulaError("División por cero")
        
        return result

    @staticmethod
    def _apply_operator(output: List[float], operator: str):
        """Aplica un operador a la pila"""
        if len(output) < 2:
            raise FormulaError(f"Operador '{operator}' requiere dos operandos")
        b = output.pop()
        a = output.pop()
        result = FormulaParser.OPERATORS[operator][1](a, b)
        if result is None:
            raise FormulaError("División por cero")
        output.append(result)

    @staticmethod
    def _apply_function(output: List[float], func_name: str):
        """Aplica una función a la pila"""
        if func_name in ('IF', 'SI'):
            # IF(condicion; valor_si_verdadero; valor_si_falso)
            if len(output) < 3:
                raise FormulaError(f"Función {func_name} requiere 3 argumentos")
            val_false = output.pop()
            val_true = output.pop()
            condition = output.pop()
            output.append(FormulaParser.FUNCTIONS[func_name](condition, val_true, val_false))
        elif func_name == 'ROUND':
            if len(output) < 1:
                raise FormulaError(f"Función {func_name} requiere al menos 1 argumento")
            decimals = output.pop() if len(output) >= 2 else 0
            value = output.pop()
            output.append(FormulaParser.FUNCTIONS[func_name](value, decimals))
        else:
            # MIN, MAX pueden tomar múltiples argumentos
            if len(output) < 2:
                raise FormulaError(f"Función {func_name} requiere al menos 2 argumentos")
            b = output.pop()
            a = output.pop()
            output.append(FormulaParser.FUNCTIONS[func_name](a, b))


class DependencyResolver:
    """Resuelve dependencias entre campos calculados"""
    
    @staticmethod
    def build_dependency_graph(campos: List[Any]) -> Dict[str, Set[str]]:
        """Construye grafo de dependencias"""
        graph = {}
        for campo in campos:
            if campo.modo == 'CALCULADO' and campo.formula:
                deps = FormulaParser.extract_variables(campo.formula)
                graph[campo.clave] = deps
            else:
                graph[campo.clave] = set()
        return graph

    @staticmethod
    def topological_sort(graph: Dict[str, Set[str]]) -> List[str]:
        """Ordena campos por dependencias usando DFS"""
        visited = set()
        temp_mark = set()
        result = []
        
        def visit(node):
            if node in temp_mark:
                raise FormulaError("Dependencia circular detectada")
            if node in visited:
                return
            
            temp_mark.add(node)
            
            # Visitar dependencias primero
            for dep in graph.get(node, []):
                if dep in graph:  # Solo si la dependencia existe como campo
                    visit(dep)
            
            temp_mark.remove(node)
            visited.add(node)
            result.append(node)
        
        # Visitar todos los nodos
        for node in graph:
            if node not in visited:
                visit(node)
        
        return result

    @staticmethod
    def detect_cycles(graph: Dict[str, Set[str]]) -> List[str]:
        """Detecta ciclos en el grafo"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in graph:
                    continue
                    
                if neighbor not in visited:
                    if has_cycle(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Encontramos un ciclo
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:]
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                result = has_cycle(node, [])
                if result:
                    return result if isinstance(result, list) else [node]
        
        return []


class FormulaEngine:
    """Motor principal de evaluación de fórmulas"""
    
    @staticmethod
    def validate_formula(formula: str, available_vars: Set[str], strict: bool = False) -> Tuple[bool, str]:
        """Valida una fórmula
        
        Args:
            formula: Fórmula a validar
            available_vars: Variables disponibles
            strict: Si True, valida que todas las variables existan. Si False, solo valida sintaxis.
        """
        try:
            if not formula or not formula.strip():
                return False, "Fórmula vacía"
            
            variables = FormulaParser.extract_variables(formula)
            
            if strict:
                missing = variables - available_vars
                if missing:
                    return False, f"Variables no definidas: {', '.join(missing)}"
            
            # Intentar parsear (validar sintaxis)
            FormulaParser.tokenize(formula)
            return True, "OK"
        
        except Exception as e:
            return False, str(e)

    @staticmethod
    def calculate(campos: List[Any], inputs: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Calcula todos los campos de una plantilla.
        Retorna (outputs, errores)
        """
        outputs = {}
        errores = {}
        
        # Construir grafo de dependencias
        try:
            graph = DependencyResolver.build_dependency_graph(campos)
            order = DependencyResolver.topological_sort(graph)
        except FormulaError as e:
            cycles = DependencyResolver.detect_cycles(
                DependencyResolver.build_dependency_graph(campos)
            )
            if cycles:
                cycle_str = ' → '.join(cycles) + ' → ' + cycles[0]
                return {}, {'_global': f'Dependencia circular detectada: {cycle_str}'}
            else:
                return {}, {'_global': f'Error en dependencias: {str(e)}'}
        
        # Preparar valores disponibles
        values = {}
        
        # Agregar inputs manuales (con conversión de unidades)
        for campo in campos:
            if campo.modo == 'MANUAL':
                if campo.clave in inputs:
                    val = inputs[campo.clave]
                    if campo.tipo == 'number':
                        try:
                            num_val = float(val) if val != '' else 0
                            # Convertir a mm si tiene unidad de longitud
                            if campo.unidad in ('cm', 'm'):
                                from ..models import CampoPlantilla
                                num_val *= CampoPlantilla.CONVERSION_TO_MM.get(campo.unidad, 1)
                            values[campo.clave] = num_val
                        except (ValueError, TypeError):
                            errores[campo.clave] = f"Valor inválido para número: {val}"
                    else:
                        values[campo.clave] = val
                elif campo.requerido:
                    errores[campo.clave] = "Campo requerido"
        
        # Calcular campos en orden de dependencias
        for clave in order:
            campo = next((c for c in campos if c.clave == clave), None)
            if not campo:
                continue
            
            if campo.modo == 'CALCULADO' and campo.formula:
                try:
                    result = FormulaParser.evaluate(campo.formula, values)
                    values[campo.clave] = result
                    outputs[campo.clave] = result
                except FormulaError as e:
                    errores[campo.clave] = str(e)
                except Exception as e:
                    errores[campo.clave] = f"Error: {str(e)}"
            elif campo.modo == 'MANUAL':
                outputs[campo.clave] = values.get(campo.clave, '')
        
        return outputs, errores
