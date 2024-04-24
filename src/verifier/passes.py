from verifier.analyzer import *
from data.transform import *
from model.llm import *
from model.utils import *
import re
import json


class Passes:
    def __init__(self, online_model_name, key, spec_file_name):
        self.online_model_name = online_model_name
        self.key = key
        self.spec_file_name = spec_file_name
        self.model = LLM(self.online_model_name, self.key, 0)

    # Symbolic Analysis
    def statement_check(self, ts_analyzer: TSAnalyzer, trace: List[Tuple[int, str]]):
        debug_print("Start statement check")

        if len(trace) < 2:
            debug_print("Trace is shorter than 2. Failed!")
            return False

        (src_line_number, src_name) = trace[0]
        (sink_line_number, sink_name) = trace[-1]

        # Check whether the lines are the first line of the function
        source_functions = ts_analyzer.find_function_by_line_number(src_line_number)
        if len(source_functions) == 1:
            if source_functions[0].start_line_number == src_line_number:
                return False

        sink_functions = ts_analyzer.find_function_by_line_number(sink_line_number)
        if len(sink_functions) == 1:
            if sink_functions[0].start_line_number == sink_line_number:
                return False

        # Check the syntax consistency
        src_list = ts_analyzer.find_node_by_line_number(src_line_number)
        src_syntactic_types = ts_analyzer.collect_syntactic_types(src_list)

        sink_list = ts_analyzer.find_node_by_line_number(sink_line_number)
        sink_syntactic_types = ts_analyzer.collect_syntactic_types(sink_list)

        with open(
                Path(__file__).resolve().parent.parent / "prompt" / self.spec_file_name,
                "r",
        ) as read_file:
            spec = json.load(read_file)
        example_strs = spec["analysis_examples"]

        (example_src_syntactic_types, example_sink_syntactic_types) = (
            self.analyze_examples_str(ts_analyzer, example_strs)
        )

        debug_print("src_syntactic_types: ", src_syntactic_types)
        debug_print("sink_syntactic_types: ", sink_syntactic_types)
        debug_print("example_src_syntactic_types: ", example_src_syntactic_types)
        debug_print("example_sink_syntactic_types: ", example_sink_syntactic_types)

        if (
                example_src_syntactic_types.isdisjoint(src_syntactic_types)
                # and len(src_syntactic_types) > 0
        ) or (
                example_sink_syntactic_types.isdisjoint(sink_syntactic_types)
                # and len(sink_syntactic_types) > 0
        ):
            return False
        return True

    # Neural Analysis
    def function_check(self, ts_analyzer: TSAnalyzer, trace: List[Tuple[int, str]], is_measure_token_cost: bool = False):
        debug_print("Start function check")

        output_results = {
            "src code": "",
            "sink code": "",
            "src response": "",
            "sink response": "",
            "trace": trace,
            "all program size": 0,
            "is_src": False,
            "is_sink": False,
            "input_token_cost": 0,
            "output_token_cost": 0,
        }

        if len(trace) < 2:
            debug_print("Trace is shorter than 2. Failed!")
            return False, output_results

        (src_line_number, src_name) = trace[0]
        (sink_line_number, sink_name) = trace[-1]

        with open(
                Path(__file__).resolve().parent.parent / "prompt" / self.spec_file_name, "r"
        ) as read_file:
            spec = json.load(read_file)

        #  Check source
        source_functions = ts_analyzer.find_function_by_line_number(src_line_number)
        if len(source_functions) != 1:
            debug_print("DO not find function?")
            debug_print(source_functions)
            return True, output_results

        source_function = source_functions[0]
        message = "\n".join(spec["meta_prompts_in_function_src_check"])
        src_example = "\n".join(spec["source_examples"])
        src_line_number_in_function = str(
            src_line_number - source_function.start_line_number + 1
        )
        message = (
            message.replace(
                "<SRC_PROGRAM>", add_line_numbers(source_function.function_code)
            )
            .replace("<SRC_EXAMPLES>", src_example)
            .replace("<SRC_LINE_NUMBER>", src_line_number_in_function)
            .replace("<SRC_SYMBOL>", src_name)
        )

        output, input_token_cost, output_token_cost = self.model.infer(message, is_measure_token_cost)

        debug_print("Checking the first function")
        debug_print("message: \n", message)
        debug_print("output: ", output)

        is_source = self.get_yes_or_no(output)
        output_results["src code"] = add_line_numbers(source_function.function_code)
        output_results["all program size"] += len(source_function.function_code.split("\n"))
        output_results["src response"] = output
        output_results["is_src"] = is_source
        output_results["input_token_cost"] += input_token_cost
        output_results["output_token_cost"] += output_token_cost

        if not is_source:
            debug_print("output: ", output)
            return False, output_results

        # Check sink
        is_sink = True
        sink_functions = ts_analyzer.find_function_by_line_number(sink_line_number)
        if len(sink_functions) != 1:
            debug_print(sink_line_number)
            debug_print("DO not find function?")
            return True, output_results

        sink_function = sink_functions[0]
        message = "\n".join(spec["meta_prompts_in_function_sink_check"])
        sink_example = "\n".join(spec["sink_examples"])
        sink_line_number_in_function = str(
            sink_line_number - sink_function.start_line_number + 1
        )
        message = (
            message.replace(
                "<SINK_PROGRAM>", add_line_numbers(sink_function.function_code)
            )
            .replace("<SINK_EXAMPLES>", sink_example)
            .replace("<SINK_LINE_NUMBER>", sink_line_number_in_function)
            .replace("<SINK_SYMBOL>", sink_name)
        )

        output, input_token_cost, output_token_cost = self.model.infer(message, is_measure_token_cost)
        output_results["input_token_cost"] += input_token_cost
        output_results["output_token_cost"] += output_token_cost

        debug_print("Checking the last function")
        debug_print("message: \n", message)
        debug_print("output: ", output)

        if "no" in output.split("\n")[-1].lower() and "yes" not in output.split("\n")[-1].lower():
            is_sink = False

        output_results["sink code"] = add_line_numbers(source_function.function_code)
        output_results["all program size"] += len(sink_function.function_code.split("\n"))
        output_results["sink response"] = output
        output_results["is_sink"] = is_sink

        if not is_sink:
            debug_print("output: ", output)
            return False, output_results
        return True, output_results

    # Symbolic Analysis
    def call_graph_check(self, ts_analyzer: TSAnalyzer, trace: List[Tuple[int, str]]):
        def get_parents(graph, start):
            visited = set()  # Set to keep track of visited nodes
            stack = [start]  # Stack for DFS traversal
            while stack:
                node = stack.pop()
                if node not in visited:
                    visited.add(node)
                    neighbors = graph.get(node, [])  # Get neighbors of the current node
                    stack.extend(neighbors)
            return visited

        debug_print("Start call graph check")

        if len(trace) < 2:
            debug_print("Trace is shorter than 2. Failed!")
            return False

        function_ids_in_trace = []

        for line_number, var_expr_name in trace:
            functions = ts_analyzer.find_function_by_line_number(line_number)
            if len(functions) != 1:
                return True
            function = functions[0]
            function_ids_in_trace.append((line_number, function.function_id))

        if len(set(function_ids_in_trace)) == 1:
            return True

        for i in range(len(function_ids_in_trace) - 1):
            (pre_line_number, pre_function_id) = function_ids_in_trace[i]
            (post_line_number, post_function_id) = function_ids_in_trace[i + 1]

            if pre_function_id == post_function_id:
                continue

            pre_function_parents = get_parents(
                ts_analyzer.callee_caller_map, pre_function_id
            )
            post_function_parents = get_parents(
                ts_analyzer.callee_caller_map, post_function_id
            )

            debug_print(pre_function_parents)
            debug_print(post_function_parents)

            if pre_function_id in post_function_parents or post_function_id in pre_function_parents:
                continue

            # might be too weak
            common_ancestors = pre_function_parents.intersection(post_function_parents)
            if len(common_ancestors) == 0:
                debug_print(
                    "The following two functions are independent: ",
                    ts_analyzer.environment[pre_function_id].function_name,
                    ts_analyzer.environment[post_function_id].function_name,
                )
                return False
            else:
                # Consider the side effect
                for common_ancestor in common_ancestors:
                    for sub_common_ancestor in ts_analyzer.caller_callee_map[common_ancestor]:
                        sub_common_ancestor_code = ts_analyzer.environment[sub_common_ancestor].function_code
                        first_line = sub_common_ancestor_code.split("\n")[0]
                        if "void" not in first_line or "()" not in first_line:
                            return True
                return False
        return True

    # Symbolic Analysis
    def control_flow_check(self, ts_analyzer: TSAnalyzer, trace: List[Tuple[int, str]]):
        debug_print("Start control flow check")

        if len(trace) < 2:
            debug_print("Trace is shorter than 2. Failed!")
            return False

        locations = []
        for line_number, var_expr_name in trace:
            functions = ts_analyzer.find_function_by_line_number(line_number)
            if len(functions) != 1:
                return True
            function = functions[0]
            locations.append((function.function_id, line_number))

        for i in range(len(locations) - 1):
            (pre_function_id, pre_line_number) = locations[i]
            (post_function_id, post_line_number) = locations[i + 1]
            currrent_function = ts_analyzer.environment[pre_function_id]
            pre_line_number_in_function = (
                    pre_line_number - currrent_function.start_line_number + 1
            )
            post_line_number_in_function = (
                    post_line_number - currrent_function.start_line_number + 1
            )

            if pre_function_id != post_function_id:
                continue

            if pre_line_number_in_function == post_line_number_in_function:
                continue

            if self.is_must_unreachable(
                    pre_line_number_in_function,
                    post_line_number_in_function,
                    currrent_function,
            ):
                debug_print(
                    "The following two lines do not conform to control flow order: \n",
                    "line",
                    pre_line_number_in_function,
                    "in",
                    ts_analyzer.environment[pre_function_id].function_name,
                    "\n",
                    "line",
                    post_line_number_in_function,
                    "in",
                    ts_analyzer.environment[pre_function_id].function_name,
                    "\n",
                )
                return False
        return True

    # Neural Analysis
    def intra_data_flow_check(
            self, ts_analyzer: TSAnalyzer, trace: List[Tuple[int, str]],
            is_measure_token_cost: bool = False
    ):
        debug_print("Start data flow check")

        output_results = {
            "trace": trace,
            "all program size": 0,
            "wrong_flow_function": "",
            "wrong_flow_start_line_number": -1,
            "wrong_flow_end_line_number": -1,
            "wrong_flow_response": "",
            "input_token_cost": 0,
            "output_token_cost": 0
        }

        if len(trace) < 2:
            debug_print("Trace is shorter than 2. Failed!")
            return False, output_results

        with open(
                Path(__file__).resolve().parent.parent / "prompt" / self.spec_file_name,
                "r",
        ) as read_file:
            spec = json.load(read_file)

        locations = []
        for line_number, var_expr_name in trace:
            functions = ts_analyzer.find_function_by_line_number(line_number)
            if len(functions) != 1:
                return True, output_results
            function = functions[0]
            locations.append((var_expr_name, function.function_id, line_number))

        for i in range(len(locations) - 1):
            (pre_var_expr_name, pre_function_id, pre_line_number) = locations[i]
            (post_var_expr_name, post_function_id, post_line_number) = locations[i + 1]

            if pre_function_id != post_function_id:
                continue

            if pre_line_number == post_line_number:
                continue

            pre_line_number_in_function = (
                    pre_line_number
                    - ts_analyzer.environment[pre_function_id].start_line_number
                    + 1
            )
            post_line_number_in_function = (
                    post_line_number
                    - ts_analyzer.environment[post_function_id].start_line_number
                    + 1
            )

            function_name = ts_analyzer.environment[pre_function_id].function_name

            function_code = add_line_numbers(
                ts_analyzer.environment[pre_function_id].function_code
            )
            output_results["all program size"] += len(function_code.split("\n"))
            print(function_code)

            pre_line_str = function_code.split("\n")[pre_line_number_in_function - 1]
            pre_line_str = " ".join(pre_line_str.split(" ")[1:]).strip()
            post_line_str = function_code.split("\n")[post_line_number_in_function - 1]
            post_line_str = " ".join(post_line_str.split(" ")[1:]).strip()

            if pre_var_expr_name not in pre_line_str or post_var_expr_name not in post_line_str:
                print(pre_var_expr_name)
                print(pre_line_str)
                print(post_var_expr_name)
                print(post_line_str)
                # if "()" not in pre_line_str and "()" not in post_line_str:
                #     exit(0)
                return False, output_results

            message = "\n".join(spec["meta_prompts_in_intra_data_flow_check"])
            message = (
                message.replace("<FUNCTION>", function_code)
                .replace("<FUNCTION_NAME>", function_name)
                .replace("<PRE_LINE_NUMBER>", str(pre_line_number_in_function))
                .replace("<POST_LINE_NUMBER>", str(post_line_number_in_function))
                .replace("<PRE_SYMBOL>", pre_var_expr_name)
                .replace("<POST_SYMBOL>", post_var_expr_name)
                .replace("<PRE_LINE_STR>", pre_line_str)
                .replace("<POST_LINE_STR>", post_line_str)
                .replace("<INTRA_DATA_FLOW_EXAMPLES>", "\n".join(spec["intra_data_flow_examples"]))
            )
            output, input_token_cost, output_token_cost = self.model.infer(message, is_measure_token_cost)

            output_results["input_token_cost"] += input_token_cost
            output_results["output_token_cost"] += output_token_cost

            debug_print("Checking the function ", function_name)
            debug_print("message: \n", message)
            debug_print("output: ", output)

            line_numbers_in_output = set(map(int, re.findall(r"\b\d+\b", output)))

            if (
                    pre_line_number_in_function not in line_numbers_in_output
                    or post_line_number_in_function not in line_numbers_in_output
            ):
                debug_print("pre_line_number_in_function", pre_line_number_in_function)
                debug_print("post_line_number_in_function", post_line_number_in_function)
                debug_print("output: ", output)
                return False, output_results

            is_flow = self.get_yes_or_no(output)

            if not is_flow:
                output_results["wrong_flow_function"] = function_name
                output_results["wrong_flow_start_line_number"] = pre_line_number
                output_results["wrong_flow_end_line_number"] = post_line_number
                output_results["wrong_flow_response"] = output
                debug_print(message)
                debug_print("output: ", output)
                return False, output_results
        return True, output_results

    # Neural Analysis, deprecated
    def escape_check(self, ts_analyzer: TSAnalyzer, trace: List[Tuple[int, str]], is_measure_token_cost: bool = False):
        debug_print("Start escape check")

        if len(trace) < 2:
            debug_print("Trace is shorter than 2. Failed!")
            return False

        function_ids_in_trace = []
        for line_number, var_expr_name in trace:
            functions = ts_analyzer.find_function_by_line_number(line_number)
            if len(functions) != 1:
                return True
            function = functions[0]
            function_ids_in_trace.append(function.function_id)

        if len(set(function_ids_in_trace)) == 1:
            return True

        with open(
                Path(__file__).resolve().parent.parent / "prompt" / self.spec_file_name,
                "r",
        ) as read_file:
            spec = json.load(read_file)

        for line_number, var_expr_name in trace[:-1]:
            functions = ts_analyzer.find_function_by_line_number(line_number)
            if len(functions) != 1:
                return True
            function = functions[0]
            node_list = ts_analyzer.find_node_by_line_number(line_number)
            syntactic_types = ts_analyzer.collect_syntactic_types(node_list)
            if "assignment_expression" not in syntactic_types:
                continue

            message = "\n".join(spec["meta_prompts_in_escape_check"])
            line_number_in_function = line_number - function.start_line_number + 1

            message = (
                message.replace("<FUNCTION>", add_line_numbers(function.function_code))
                .replace("<FUNCTION_NAME>", function.function_name)
                .replace("<LINE_NUMBER>", str(line_number_in_function))
            )
            output, input_token_cost, output_token_cost = self.model.infer(message, is_measure_token_cost)

            # debug_print("Checking the function: ", function.function_name)
            # debug_print("message: \n", message)
            # debug_print("output: ", output)

            if "no" in output.split("\n")[-1].lower() and "yes" not in output.split("\n")[-1].lower():
                debug_print("message: \n", message)
                debug_print("output: ", output)
                return False
        return True

    def analyze_examples_str(
            self, ts_analyzer: TSAnalyzer, example_str_list: List[str]
    ):
        pattern = r"Example (.+?)END REPORT----------------\n"
        matches = re.findall(pattern, "\n".join(example_str_list), re.DOTALL)

        cwd = Path(__file__).resolve().parent.absolute()
        TSPATH = cwd / "../../lib/build/"
        language_path = TSPATH / "my-languages.so"
        java_lang: Language = Language(str(language_path), "java")
        parser: tree_sitter.Parser = tree_sitter.Parser()
        parser.set_language(java_lang)

        src_syntactic_types = set([])
        sink_syntactic_types = set([])

        for match in matches:
            code_pattern = r"```(.+?)```"
            code_list = re.findall(code_pattern, match, re.DOTALL)
            example_code = re.sub(r"^\d+\.\s*", "", code_list[0], flags=re.MULTILINE)

            trace_pattern = r"\[Trace:(.+?)]"
            trace_match = re.search(trace_pattern, match)
            trace = trace_match.group(1).strip()
            # Extract line numbers using regular expression
            line_numbers = re.findall(r"Line (\d+)", trace)

            # Get the first and last line numbers
            first_line = int(line_numbers[0])
            last_line = int(line_numbers[-1])

            tree: tree_sitter.Tree = parser.parse(bytes(example_code, "utf8"))
            root_node: tree_sitter.Node = tree.root_node
            all_nodes = TSAnalyzer.find_all_nodes(root_node)

            src_node_list = []
            for node in all_nodes:
                start_line = example_code[: node.start_byte].count("\n")
                end_line = example_code[: node.end_byte].count("\n")
                if start_line == end_line == first_line:
                    src_node_list.append((example_code, node))
            src_syntactic_types = src_syntactic_types.union(
                set(ts_analyzer.collect_syntactic_types(src_node_list))
            )

            sink_node_list = []
            for node in all_nodes:
                start_line = example_code[: node.start_byte].count("\n")
                end_line = example_code[: node.end_byte].count("\n")
                if start_line == end_line == last_line:
                    sink_node_list.append((example_code, node))
            sink_syntactic_types = sink_syntactic_types.union(
                set(ts_analyzer.collect_syntactic_types(sink_node_list))
            )
        return src_syntactic_types, sink_syntactic_types

    def is_must_unreachable(
            self, src_line_number: int, sink_line_number: int, function: Function
    ) -> bool:
        src_line_number_in_function = src_line_number - function.start_line_number + 1
        sink_line_number_in_function = sink_line_number - function.start_line_number + 1

        for condition_line, if_statement_end_line in function.if_statements:
            (
                _,
                _,
                (true_branch_start_line, true_branch_end_line),
                (else_branch_start_line, else_branch_end_line),
            ) = function.if_statements[(condition_line, if_statement_end_line)]
            if (
                    true_branch_start_line
                    <= src_line_number_in_function
                    <= true_branch_end_line
                    and else_branch_start_line
                    <= sink_line_number_in_function
                    <= else_branch_end_line
            ):
                return True
            if (
                    true_branch_start_line
                    <= src_line_number_in_function
                    <= true_branch_end_line
                    and else_branch_start_line
                    <= sink_line_number_in_function
                    <= else_branch_end_line
            ):
                return True
        if src_line_number_in_function >= sink_line_number_in_function:
            debug_print(src_line_number_in_function, " --> ", sink_line_number_in_function)
            return True
        return False

    def get_yes_or_no(self, output: str):
        lines = output.strip().splitlines()  # Split the paragraph into a list of lines
        lines.reverse()  # Reverse the order of lines
        line = ""
        for line in lines:
            if "yes" in line.lower() or "no" in line.lower():
                print(line.strip())
                break  # Stop iterating once a matching line is found
        return "no" not in line.lower()
