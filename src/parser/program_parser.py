import os
import sys
from os import path
from pathlib import Path
from typing import List, Tuple, Dict, Set

import tree_sitter
from tree_sitter import Language
from tqdm import tqdm
import networkx as nx

sys.path.append(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))

from typing import List, Tuple, Dict

class Function:
    def __init__(
        self,
        function_id: int,
        function_name: str,
        function_code: str,
        start_line_number: int,
        end_line_number: int,
        function_node: tree_sitter.Node,
    ) -> None:
        """
        Record basic facts of the function
        """
        self.function_id = function_id
        self.function_name = function_name
        self.function_code = function_code
        self.start_line_number = start_line_number
        self.end_line_number = end_line_number

        # Attention: the parse tree is in the context of the whole file
        self.parse_tree_root_node = function_node  # root node of the parse tree of the current function
        self.call_site_nodes = []   # call site info

        ## Results of AST node type analysis
        self.paras = set([])        # A set of (Expr, int) tuples, where int indicates the index of the parameter

        ## Results of intraprocedural control flow analysis
        self.if_statements = {}     # if statement info
        self.loop_statements = {}   # loop statement info


class TSParser:
    """
    TSParser class for extracting information from source files using tree-sitter.
    """

    def __init__(self, code_in_projects: Dict[str, str], language_setting: str) -> None:
        """
        Initialize TSParser with a collection of source files.
        :param code_in_projects: A dictionary containing the content of source files.
        """
        self.code_in_projects = code_in_projects
        self.language_setting = language_setting

        cwd = Path(__file__).resolve().parent.absolute()
        TSPATH = cwd / "../../lib/build/"
        language_path = TSPATH / "my-languages.so"
        self.language = Language(str(language_path), "go")

        self.functionRawDataDic = {}
        self.functionNameToId = {}
        self.functionToFile = {}
        self.fileContentDic = {}

        # Initialize the parser
        self.parser = tree_sitter.Parser()
        self.parser.set_language(self.language)


    def parse_function_info(self, file_path: str, source_code: str, tree: tree_sitter.Tree) -> None:
        """
        Parse the function information in a source file.
        :param file_path: The path of the source file.
        :param source_code: The content of the source file.
        :param tree: The parse tree of the source file.
        """
        assert self.language_setting == "Go"
        all_function_nodes = TSAnalyzer.find_nodes_by_type(tree.root_node, "function_declaration")
        all_method_nodes = TSAnalyzer.find_nodes_by_type(tree.root_node, "method_declaration")
        all_function_nodes.extend(all_method_nodes)

        for function_node in all_function_nodes:
            function_name = ""
            for sub_node in function_node.children:
                if sub_node.type in {"identifier", "field_identifier"}:
                    function_name = source_code[sub_node.start_byte:sub_node.end_byte]
                    break

            if function_name == "":
                continue
            
            # Initialize the raw data of a function
            start_line_number = source_code[: function_node.start_byte].count("\n") + 1
            end_line_number = source_code[: function_node.end_byte].count("\n") + 1
            function_id = len(self.functionRawDataDic) + 1
            
            self.functionRawDataDic[function_id] = (
                function_name,
                start_line_number,
                end_line_number,
                function_node
            )
            self.functionToFile[function_id] = file_path
            
            if function_name not in self.functionNameToId:
                self.functionNameToId[function_name] = set([])
            self.functionNameToId[function_name].add(function_id)
        return
    

    def parse_project(self) -> None:
        """
        Parse the project.
        """
        pbar = tqdm(total=len(self.code_in_projects), desc="Parsing files")
        for file_path in self.code_in_projects:
            pbar.update(1)
            source_code = self.code_in_projects[file_path]
            tree = self.parser.parse(bytes(source_code, "utf8"))
            self.parse_function_info(file_path, source_code, tree)
            self.fileContentDic[file_path] = source_code
        return


class TSAnalyzer:
    """
    TSAnalyzer class for retrieving necessary facts or functions for LMAgent
    """

    def __init__(
        self,
        code_in_projects: Dict[str, str],
        language: str,
    ) -> None:
        """
        Initialize TSParser with the project path.
        :param code_in_projects: A dictionary mapping file paths of source files to their contents
        """
        self.code_in_projects = code_in_projects
        self.ts_parser = TSParser(self.code_in_projects, language)
        self.ts_parser.parse_project()

        # Each funcntion in the environments maintains the local meta data, including
        # (1) AST node type analysis
        # (2) intraprocedural control flow analysis
        self.environment = {}  

        # Results of call graph analysis
        self.caller_callee_map = {}
        self.callee_caller_map = {}
        self.call_graph = nx.DiGraph()

        pbar = tqdm(total=len(self.ts_parser.functionRawDataDic), desc="Analyzing functions")
        for function_id in self.ts_parser.functionRawDataDic:
            pbar.update(1)
            (name, start_line_number, end_line_number, function_node) = (
                self.ts_parser.functionRawDataDic[function_id]
            )
            file_name = self.ts_parser.functionToFile[function_id]
            file_content = self.ts_parser.fileContentDic[file_name]
            function_code = file_content[function_node.start_byte:function_node.end_byte]
            current_function = Function(
                function_id, name, function_code, start_line_number, end_line_number, function_node
            )
            current_function = self.extract_meta_data_in_single_function(current_function, file_content)
            self.environment[function_id] = current_function
        pbar.close()

        pbar = tqdm(total=len(self.ts_parser.functionRawDataDic), desc="Analyzing call graphs")
        for function_id in self.environment:
            pbar.update(1)
            file_name = self.ts_parser.functionToFile[function_id]
            file_content = self.ts_parser.fileContentDic[file_name]
            current_function = self.environment[function_id]
            self.extract_call_graph(current_function, file_content)
        pbar.close()

        # initialize call graph
        for caller_id in self.caller_callee_map:
            for callee_id in self.caller_callee_map[caller_id]:
                self.call_graph.add_edge(caller_id, callee_id)
        return
    

    def extract_meta_data_in_single_function(
        self, current_function: Function, file_content: str
    ) -> Function:
        """
        Extract meta data in a single function
        :param current_function: the function to be analyzed
        :param file_content: the content of the file
        """
        # AST node type analysis
        current_function.paras = self.find_paras(current_function, file_content)
        current_function.retsmts = self.find_retstmts(current_function, file_content)

        # Intraprocedural control flow analysis
        current_function.if_statements = self.find_if_statements(
            file_content,
            current_function.parse_tree_root_node,
        )

        current_function.loop_statements = self.find_loop_statements(
            file_content,
            current_function.parse_tree_root_node,
        )

        return current_function

    #################################################
    ########## Call Graph Analysis ##################
    #################################################
    def extract_call_graph(self, current_function: Function, file_content: str):
        """
        Extract the call graph.
        :param current_function: the function to be analyzed
        :param file_content: the content of the file
        """
        # Over-approximate the caller-callee relationship via function names, achieved by find_callee
        function_call_node_type = "call_expression"
        all_call_sites = self.find_nodes_by_type(current_function.parse_tree_root_node, function_call_node_type)
        white_call_sites = []

        for call_site_node in all_call_sites:
            callee_ids = self.find_callee(file_content, call_site_node)
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
                white_call_sites.append(call_site_node)

        current_function.call_site_nodes = white_call_sites
        return

    @staticmethod
    def get_callee_name_at_call_site(node: tree_sitter.Node, source_code: str, language: str) -> str:
        """
        Get the callee name at the call site.
        :param node: the node of the call site
        :param source_code: the content of the file
        :param language: the language of the source code
        """
        assert node.type == "call_expression"
        for sub_node in node.children:
            if sub_node.type == "selector_expression":
                for sub_node in sub_node.children:
                    if sub_node.type == "field_identifier":
                        return source_code[sub_node.start_byte:sub_node.end_byte]
        return ""
    
    @staticmethod
    def get_arguments_at_call_site(node: tree_sitter.Node, source_code: str) -> List[str]:
        """
        Get arguments at the call site.
        :param node: the node of the call site
        :param source_code: the content of the file
        """
        arguments = []
        for sub_node in node.children:
            if sub_node.type == "argument_list":
                arg_list = sub_node.children[1:-1]
                for element in arg_list:
                    if element.type != ",":
                        arguments.append(source_code[element.start_byte:element.end_byte])
        return arguments
    

    def find_callee(self, file_content: str, call_site_node: tree_sitter.Node) -> List[int]:
        """
        Find the callee function of the call site.
        :param file_content: the content of the file
        :param call_site_node: the node of the call site
        """
        callee_name = self.get_callee_name_at_call_site(call_site_node, file_content, self.ts_parser.language_setting)
        arguments = self.get_arguments_at_call_site(call_site_node, file_content)
        temp_callee_ids = []
        
        if callee_name in self.ts_parser.functionNameToId:
            temp_callee_ids.extend(list(self.ts_parser.functionNameToId[callee_name]))
        # check parameter number and the argument number
        callee_ids = []
        for callee_id in temp_callee_ids:
            callee = self.environment[callee_id]
            paras = self.find_paras(callee, file_content)
            if len(paras) == len(arguments):
                callee_ids.append(callee_id)
        return callee_ids
    

    def get_caller_functions(self, function: Function) -> List[Function]:
        """
        Get all the caller function of the function.
        """
        callee_id = function.function_id
        if callee_id not in self.callee_caller_map.keys():
            return []
        caller_ids = self.callee_caller_map[function.function_id]
        caller = [self.environment[caller_id] for caller_id in caller_ids]
        return caller
    

    def get_callee_functions_by_name(self, function: Function, callee:str) -> List[Function]:
        """
        Get the callee function of the function with name `callee`.
        :param function: the function to be analyzed
        :param callee: the name of the callee function
        """
        if function.function_id not in self.caller_callee_map.keys():
            return []
        callee_list = []
        for callee_id in self.caller_callee_map[function.function_id]:
            if self.environment[callee_id].function_name == callee:
                callee_list.append(self.environment[callee_id])
        return callee_list

    #################################################
    ########## AST Node Type Analysis ###############
    #################################################   
    def find_paras(self, current_function: Function, file_content: str) -> Set[Tuple[str, int, int]]:
        """
        Find the parameters in the function.
        :param file_content: the content of the file
        :param node: the node of the function
        """
        paras = set([])
        # parameter_list_nodes = self.find_nodes_by_type(current_function.parse_tree_root_node, "parameter_list")

        parameter_list_nodes = []
        for sub_node in current_function.parse_tree_root_node.children:
            if sub_node.type in "parameter_list":
                parameter_list_nodes.append(sub_node)

        index = 0

        for parameter_list_node in parameter_list_nodes:
            for sub_node in parameter_list_node.children:
                if sub_node.type in "parameter_declaration":
                    for sub_sub_node in sub_node.children:
                        if sub_sub_node.type in "identifier":
                            parameter_name = file_content[sub_sub_node.start_byte:sub_sub_node.end_byte]
                            line_number = file_content[:sub_sub_node.start_byte].count("\n") + 1
                            paras.add((parameter_name, line_number, index))
                            index += 1
                            break
        return paras


    def find_retstmts(self, current_function: Function, file_content: str) -> List[Tuple[str, int]]:
        """
        Find the return statements in the function.
        :param current_function: the function to be analyzed
        :param file_content: the content of the file
        """
        retstmts = []
        retnodes = self.find_nodes_by_type(current_function.parse_tree_root_node, "return_statement")
        for retnode in retnodes:
            line_number = file_content[:retnode.start_byte].count("\n") + 1
            retstmts.append((retnode, line_number))
        return retstmts


    #################################################
    ########## Control Flow Analysis ################
    #################################################
    def find_if_statements(self, source_code, root_node) -> Dict[Tuple, Tuple]:
        """
        Find all the if statements in the function in Go programs
        :param source_code: the content of the function
        :param root_node: the root node of the parse tree
        """
        if_statement_nodes = self.find_nodes_by_type(root_node, "if_statement")
        if_statements = {}

        for if_statement_node in if_statement_nodes:
            condition_str = ""
            condition_start_line = 0
            condition_end_line = 0
            true_branch_start_line = 0
            true_branch_end_line = 0
            else_branch_start_line = 0
            else_branch_end_line = 0

            # store the types of sub_nodes of if_statement_node in a list
            sub_node_types = [sub_node.type for sub_node in if_statement_node.children]
            block_index = sub_node_types.index("block")
            true_branch_start_line = source_code[: if_statement_node.children[block_index].start_byte].count("\n") + 1
            true_branch_end_line = source_code[: if_statement_node.children[block_index].end_byte].count("\n") + 1
            
            if "else" in sub_node_types:
                else_index = sub_node_types.index("else")
                else_branch_start_line = source_code[: if_statement_node.children[else_index + 1].start_byte].count("\n") + 1
                else_branch_end_line = source_code[: if_statement_node.children[else_index + 1].end_byte].count("\n") + 1
            else:
                else_branch_start_line = 0
                else_branch_end_line = 0
            condition_start_line = source_code[: if_statement_node.children[block_index - 1].start_byte].count("\n") + 1
            condition_end_line = source_code[: if_statement_node.children[block_index - 1].end_byte].count("\n") + 1
            condition_str = source_code[if_statement_node.children[block_index - 1].start_byte: if_statement_node.children[block_index - 1].end_byte]
            
            if_statement_start_line = source_code[: if_statement_node.start_byte].count("\n") + 1
            if_statement_end_line = source_code[: if_statement_node.end_byte].count("\n") + 1
            line_scope = (if_statement_start_line, if_statement_end_line)
            
            info = (
                        condition_start_line,
                        condition_end_line,
                        condition_str,
                        (true_branch_start_line, true_branch_end_line),
                        (else_branch_start_line, else_branch_end_line),
                    )
            if_statements[line_scope] = info 
        return if_statements


    def find_loop_statements(self, source_code, root_node) -> Dict[Tuple, Tuple]:
        loop_statements = {}
        for_statement_nodes = self.find_nodes_by_type(root_node, "for_statement")

        for loop_node in for_statement_nodes:
            loop_start_line = source_code[: loop_node.start_byte].count("\n") + 1
            loop_end_line = source_code[: loop_node.end_byte].count("\n") + 1

            header_line_start = 0
            header_line_end = 0
            header_str = ""
            loop_body_start_line = 0
            loop_body_end_line = 0

            if len(loop_node.children) == 3:
                loop_body_start_line = source_code[: loop_node.children[2].start_byte].count("\n") + 1
                loop_body_end_line = source_code[: loop_node.children[2].end_byte].count("\n") + 1
                header_line_start = source_code[: loop_node.children[1].start_byte].count("\n") + 1
                header_line_end = source_code[: loop_node.children[1].end_byte].count("\n") + 1
                header_str = source_code[loop_node.children[1].start_byte: loop_node.children[1].end_byte]
            else:
                loop_body_start_line = source_code[: loop_node.children[1].start_byte].count("\n") + 1
                loop_body_end_line = source_code[: loop_node.children[1].end_byte].count("\n") + 1
                header_line_start = loop_start_line
                header_line_end = loop_start_line
                header_str = ""

            loop_statements[(loop_start_line, loop_end_line)] = (
                header_line_start,
                header_line_end,
                header_str,
                loop_body_start_line,
                loop_body_end_line,
            )
        return loop_statements

    #################################################
    ########## Control Order Analysis ################
    #################################################
    @staticmethod
    def check_control_order(function: Function, src_line_number: str, sink_line_number: str) -> bool:
        """
        If the function return True, the line src_line_number may be execeted before the line sink_line_number.
        The semantics of return statements are not considered.
        This is an over-approximation of the control order.
        """
        src_line_number_in_function = src_line_number
        sink_line_number_in_function = sink_line_number

        if src_line_number_in_function == sink_line_number_in_function:
            return True

        # Consider branches, return false if src and sink in different branches
        for if_statement_start_line, if_statement_end_line in function.if_statements:
            (
                _,
                _,
                _,
                (true_branch_start_line, true_branch_end_line),
                (else_branch_start_line, else_branch_end_line),
            ) = function.if_statements[(if_statement_start_line, if_statement_end_line)]
            if (
                true_branch_start_line
                <= src_line_number_in_function
                <= true_branch_end_line
                and else_branch_start_line
                <= sink_line_number_in_function
                <= else_branch_end_line
                and else_branch_start_line != 0
                and else_branch_end_line != 0
            ):
                return False
            
        # Consider loops
        if src_line_number_in_function > sink_line_number_in_function:
            for loop_start_line, loop_end_line in function.loop_statements:
                (                
                    _,
                    _,
                    _,
                    loop_body_start_line,
                    loop_body_end_line,
                ) = function.loop_statements[(loop_start_line, loop_end_line)]
                if (
                    loop_body_start_line
                    <= src_line_number_in_function
                    <= loop_body_end_line
                    and loop_body_start_line
                    <= sink_line_number_in_function
                    <= loop_body_end_line
                ):
                    return True
            return False
        return True
    
    #######################################################
    ########## Control reachability Analysis ##############
    #######################################################
    @staticmethod
    def check_control_reachability(function: Function, src_line_number: str, sink_line_number: str) -> bool:
        """
        If the function return True, the line src_line_number may be execeted before the line sink_line_number.
        The semantics of return statements are considered.
        This is an over-approximation of the control reachability.
        """
        if TSAnalyzer.check_control_order(function, src_line_number, sink_line_number) is False:
            return False
        
        # TODO: Temporarily disable the return satement check
        # for retstmt, retstmt_line_number in function.retsmts:
        #     if TSAnalyzer.check_control_order(function, src_line_number, retstmt_line_number) and \
        #         not TSAnalyzer.check_control_order(function, sink_line_number, retstmt_line_number):
        #         return False
        return True
    
    #################################################
    ########## AST visitor utility ##################
    #################################################
    @staticmethod
    def find_all_nodes(root_node: tree_sitter.Node) -> List[tree_sitter.Node]:
        if root_node is None:
            return []
        nodes = [root_node]
        for child_node in root_node.children:
            nodes.extend(TSAnalyzer.find_all_nodes(child_node))
        return nodes

    @staticmethod
    def find_nodes_by_type(
        root_node: tree_sitter.Node, node_type: str, k=0
    ) -> List[tree_sitter.Node]:
        """
        Find all the nodes with the specific type in the parse tree
        :param root_node: the root node of the parse tree
        :param node_type: the type of the nodes to be found
        """
        nodes = []
        if k > 100:
            return []
        if root_node.type == node_type:
            nodes.append(root_node)
        for child_node in root_node.children:
            nodes.extend(TSAnalyzer.find_nodes_by_type(child_node, node_type, k+1))
        return nodes

    def find_node_by_line_number(
        self, line_number: int
    ) -> List[Tuple[str, tree_sitter.Node]]:
        """
        Find the node that contains the specific line number
        :param line_number: the line number to be searched
        """
        code_node_list = []
        for function_id in self.environment:
            function = self.environment[function_id]
            if (
                not function.start_line_number
                <= line_number
                <= function.end_line_number
            ):
                continue
            all_nodes = TSAnalyzer.find_all_nodes(function.parse_tree_root_node)
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
    