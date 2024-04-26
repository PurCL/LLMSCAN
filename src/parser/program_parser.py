import sys
import os
from os import path
import tree_sitter
from tree_sitter import Language

sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))

from typing import List, Tuple, Dict
from enum import Enum
from data.transform import *
from pathlib import Path


class Function:
    def __init__(
        self,
        function_id: int,
        function_name: str,
        function_code: str,
        start_line_number: int,
        end_line_number: int,
    ) -> None:
        """
        Record basic facts of the function
        """
        self.function_id = function_id
        self.function_name = function_name
        self.function_code = function_code
        self.start_line_number = start_line_number
        self.end_line_number = end_line_number

        self.parse_tree = None
        self.is_transformed = False
        self.is_parsed = False

        # call site nodes and line numbers (conform to control flow order)
        self.call_site_nodes = []

        # if statement info
        self.if_statements = {}

    def set_parse_tree(self, parse_tree: tree_sitter.Tree) -> None:
        self.parse_tree = parse_tree
        self.is_parsed = True
        return

    def set_call_sites(self, call_sites: List[Tuple[tree_sitter.Node, int]]) -> None:
        self.call_site_nodes = call_sites
        return


class TSParser:
    """
    TSParser class for extracting information from Java files using tree-sitter.
    """

    def __init__(self, c_file_path: str) -> None:
        """
        Initialize TSParser with a java file path
        :param c_file_path: The path of a C file.
        """
        self.c_file_path = c_file_path
        self.methods = {}
        self.functionToFile = {}

        cwd = Path(__file__).resolve().parent.absolute()
        TSPATH = cwd / "../../lib/build/"
        language_path = TSPATH / "my-languages.so"
        # Load the Java language
        self.java_lang = Language(str(language_path), "c")

        # Initialize the parser
        self.parser = tree_sitter.Parser()
        self.parser.set_language(self.java_lang)

    def parse_function_info(
        self,
        file_path: str,
        source_code: str,
        tree: tree_sitter.Tree,
    ) -> None:
        """
        Extract class declaration info: class name, fields, and methods
        :param file_path: The path of the Java file.
        :param source_code: The content of the source code
        :param package_name: The package name
        :param root_node: The root node the parse tree
        """
        all_function_nodes = TSAnalyzer.find_nodes_by_type(tree.root_node, "function_definition")
        for node in all_function_nodes:
            # get function name
            method_name = ""
            for sub_node in node.children:
                if sub_node.type != "function_declarator":
                    continue
                for sub_sub_node in sub_node.children:
                    if sub_sub_node.type == "identifier":
                        method_name = source_code[sub_sub_node.start_byte:sub_sub_node.end_byte]
                        break
                if method_name != "":
                    break

            method_code = source_code[node.start_byte : node.end_byte]
            start_line_number = source_code[: node.start_byte].count("\n") + 1
            end_line_number = source_code[: node.end_byte].count("\n") + 1
            method_id = len(self.methods) + 1
            self.methods[method_id] = (
                method_name,
                method_code,
                start_line_number,
                end_line_number,
            )
            self.functionToFile[method_id] = file_path
        return

    def extract_single_file(self, file_path, source_code: str) -> None:
        # Parse the Java code
        tree = self.parser.parse(bytes(source_code, "utf8"))
        self.parse_function_info(
            file_path, source_code, tree
        )
        return


class TSAnalyzer:
    """
    TSAnalyzer class for retrieving necessary facts or functions for LMAgent
    """

    def __init__(
        self,
        c_file_path: str,
        original_code: str,
        analyzed_code: str,
        support_files: Dict[str, str],
    ) -> None:
        """
        Initialize TSParser with the project path.
        Currently we only analyze a single java file
        :param c_file_path: The path of a c file
        """
        self.c_file_path = c_file_path
        self.ts_parser = TSParser(c_file_path)
        self.original_code = original_code
        self.analyzed_code = analyzed_code
        self.support_files = support_files

        self.ts_parser.extract_single_file(self.c_file_path, self.analyzed_code)

        self.environment = {}
        self.caller_callee_map = {}
        self.callee_caller_map = {}

        print(len(self.ts_parser.methods))
        for method_id in self.ts_parser.methods:
            (name, code, start_line_number, end_line_number) = self.ts_parser.methods[method_id]
            print(name)

        for function_id in self.ts_parser.methods:
            (name, function_code, start_line_number, end_line_number) = (
                self.ts_parser.methods[function_id]
            )
            current_function = Function(
                function_id, name, function_code, start_line_number, end_line_number
            )
            current_function.parse_tree = self.ts_parser.parser.parse(
                bytes(function_code, "utf8")
            )
            current_function = self.extract_meta_data_in_single_function(
                current_function
            )
            self.environment[function_id] = current_function

        for callee_id in self.callee_caller_map:
            for caller_id in self.callee_caller_map[callee_id]:
                (callee_name, _, _, _) = (
                    self.ts_parser.methods[callee_id]
                )
                (caller_name, _, _, _) = (
                    self.ts_parser.methods[caller_id]
                )
                print(callee_name, caller_name)

        self.main_ids = self.find_all_top_functions()
        self.tmp_variable_count = 0

    def find_all_top_functions(self) -> List[int]:
        """
        Collect all the main functions, which are ready for analysis
        :return: a list of ids indicating main functions
        """
        # self.methods: Dict[int, (str, str)] = {}
        main_ids = []
        for method_id in self.ts_parser.methods:
            (name, code, start_line_number, end_line_number) = self.ts_parser.methods[
                method_id
            ]
            if code.count("\n") < 2:
                continue
            if name in {"main"}:
                main_ids.append(method_id)
        return main_ids

    def find_all_nodes(root_node: tree_sitter.Node) -> List[tree_sitter.Node]:
        if root_node is None:
            return []
        nodes = [root_node]
        for child_node in root_node.children:
            nodes.extend(TSAnalyzer.find_all_nodes(child_node))
        return nodes

    @staticmethod
    def find_nodes_by_type(
        root_node: tree_sitter.Node, node_type: str
    ) -> List[tree_sitter.Node]:
        nodes = []
        if root_node.type == node_type:
            nodes.append(root_node)
        for child_node in root_node.children:
            nodes.extend(TSAnalyzer.find_nodes_by_type(child_node, node_type))
        return nodes

    def find_callee(
        self, method_id: int, source_code: str, call_expr_node: tree_sitter.Node
    ) -> List[int]:
        """
        Find callees that invoked by a specific method.
        Attention: call_site_node should be derived from source_code directly
        :param method_id: caller function id
        :param file_path: the path of the file containing the caller function
        :param source_code: the content of the source file
        :param call_site_node: the node of the call site. The type is 'call_expression'
        :return the list of the ids of called functions
        """
        assert call_expr_node.type == "call_expression"
        method_name = ""
        method_name = source_code[call_expr_node.start_byte : call_expr_node.end_byte]
        for sub_child in call_expr_node.children:
            if sub_child.type == "identifier":
                method_name = source_code[sub_child.start_byte:sub_child.end_byte]
                break

        (caller_name, _, _, _) = self.ts_parser.methods[method_id]
        print("caller:", caller_name, "callee:", method_name)

        callee_ids = []
        for method_id in self.ts_parser.functionToFile:
            # Maybe too conservative
            (name, code, start_line_number, end_line_number) = (
                self.ts_parser.methods[method_id]
            )
            if name == method_name:
                callee_ids.append(method_id)
        return callee_ids

    def find_if_statements(self, source_code, root_node) -> Dict[Tuple, Tuple]:
        targets = self.find_nodes_by_type(root_node, "if_statement")
        if_statements = {}

        for target in targets:
            condition_str = ""
            condition_line = 0
            true_branch_start_line = 0
            true_branch_end_line = 0
            else_branch_start_line = 0
            else_branch_end_line = 0
            for sub_target in target.children:
                if sub_target.type == "parenthesized_expression":
                    condition_line = (
                        source_code[: sub_target.start_byte].count("\n") + 1
                    )
                    condition_str = source_code[
                        sub_target.start_byte : sub_target.end_byte
                    ]
                if "statement" in sub_target.type:
                    true_branch_start_line = (
                        source_code[: sub_target.start_byte].count("\n") + 1
                    )
                    true_branch_end_line = (
                        source_code[: sub_target.end_byte].count("\n") + 1
                    )
                if sub_target.type == "else_clause":
                    # TODO: nested else clauses
                    else_branch_start_line = (
                        source_code[: sub_target.start_byte].count("\n") + 1
                    )
                    else_branch_end_line = (
                        source_code[: sub_target.end_byte].count("\n") + 1
                    )
            if_statement_end_line = max(true_branch_end_line, else_branch_start_line)
            if_statements[(condition_line, if_statement_end_line)] = (
                condition_line,
                condition_str,
                (true_branch_start_line, true_branch_end_line),
                (else_branch_start_line, else_branch_end_line),
            )
            # print("------------------")
            # print(condition_line, if_statement_end_line)
            # print(condition_line)
            # print(condition_str)
            # print(true_branch_start_line, true_branch_end_line)
            # print(else_branch_start_line, else_branch_end_line)
            # print("------------------\n")
        return if_statements

    def extract_meta_data_in_single_function(
        self, current_function: Function
    ) -> Function:
        """
        :param current_function: Function object
        :return: Function object with updated parse tree and call info
        """
        tree = self.ts_parser.parser.parse(bytes(current_function.function_code, "utf8"))
        current_function.set_parse_tree(tree)
        root_node = tree.root_node

        # Identify call site info and maintain the environment
        all_call_sites = self.find_nodes_by_type(root_node, "call_expression")
        white_call_sites = []

        for call_site_node in all_call_sites:
            callee_ids = self.find_callee(current_function.function_id, current_function.function_code, call_site_node)
            if len(callee_ids) > 0:
                # Update the call graph
                for callee_id in callee_ids:
                    caller_id = current_function.function_id
                    if caller_id not in self.caller_callee_map:
                        self.caller_callee_map[caller_id] = set([])
                    self.caller_callee_map[caller_id].add(callee_id)
                    if callee_id not in self.callee_caller_map:
                        self.callee_caller_map[callee_id] = set([])
                    self.callee_caller_map[callee_id].add(caller_id)

        current_function.set_call_sites(white_call_sites)

        # compute the scope of the if-statements to guide the further path feasibility validation
        if_statements = self.find_if_statements(
            current_function.function_code,
            current_function.parse_tree.root_node,
        )
        current_function.if_statements = if_statements
        return current_function

    def find_function_by_line_number(self, line_number: int) -> List[Function]:
        for function_id in self.environment:
            function = self.environment[function_id]
            if function.start_line_number <= line_number <= function.end_line_number:
                return [function]
        return []

    def find_node_by_line_number(
        self, line_number: int
    ) -> List[Tuple[str, tree_sitter.Node]]:
        code_node_list = []
        for function_id in self.environment:
            function = self.environment[function_id]
            if (
                not function.start_line_number
                <= line_number
                <= function.end_line_number
            ):
                continue
            all_nodes = TSAnalyzer.find_all_nodes(function.parse_tree.root_node)
            for node in all_nodes:
                start_line = (
                    function.function_code[: node.start_byte].count("\n")
                    + function.start_line_number
                )
                end_line = (
                    function.function_code[: node.end_byte].count("\n")
                    + function.start_line_number
                )
                if start_line == end_line == line_number:
                    code_node_list.append((function.function_code, node))
        return code_node_list

    def collect_syntactic_types(self, node_list: List[Tuple[str, tree_sitter.Node]]):
        syntactic_types = set([])
        for code, node in node_list:
            if "expression" in node.type or "declarator" in node.type:
                sub_nodes = self.find_all_nodes(node)
                for sub_node in sub_nodes:
                    if (
                        any(char.isalpha() for char in sub_node.type)
                        and "identifier" not in sub_node.type
                        and "declarator" not in sub_node.type
                    ):
                        syntactic_types.add(sub_node.type)
        return syntactic_types