# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Google SecOps CLI case commands"""

import sys

from secops.cli.utils.formatters import output_formatter


def setup_case_command(subparsers):
    """Set up the case command parser.

    Supported subcommands:
        - get: Get details of specific cases (using --ids)
        - list: List cases with filtering and pagination
    """
    case_parser = subparsers.add_parser("case", help="Manage cases")
    case_subparsers = case_parser.add_subparsers(dest="subcommand")

    # Get command (for backward compatibility, handles --ids on main case command too)
    # Ideally, we should migrate --ids to a `get` subcommand, but keeping it on main for now to support existing usage
    case_parser.add_argument("--ids", help="Comma-separated list of case IDs")

    # List command
    list_parser = case_subparsers.add_parser("list", help="List cases")
    list_parser.add_argument(
        "--page-size", type=int, help="Maximum number of cases to return"
    )
    list_parser.add_argument(
        "--page-token", help="Token for the next page of results"
    )
    list_parser.add_argument(
        "--filter", dest="filter_query", help="Filter string to restrict results"
    )
    list_parser.add_argument("--order-by", help="Field to order results by")

    case_parser.set_defaults(func=handle_case_command)


def handle_case_command(args, chronicle):
    """Handle case command."""
    try:
        if args.ids:
            # Handle legacy behavior: secops case --ids ...
            case_ids = [id.strip() for id in args.ids.split(",")]
            result = chronicle.get_cases(case_ids)
            _output_cases(result, args.output)
            return

        if args.subcommand == "list":
            result = chronicle.list_cases(
                page_size=args.page_size,
                page_token=args.page_token,
                filter_query=args.filter_query,
                order_by=args.order_by,
            )
            output_formatter(result, args.output)
            return

        # If no subcommand and no --ids, show help
        print(
            "Error: No action specified. Use 'list' or provide '--ids'.",
            file=sys.stderr,
        )
        sys.exit(1)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _output_cases(result, output_format):
    """Helper to format and output case list."""
    # Convert CaseList to dictionary for output
    cases_dict = {
        "cases": [
            {
                "id": case.id,
                "display_name": case.display_name,
                "stage": case.stage,
                "priority": case.priority,
                "status": case.status,
                "soar_platform_info": (
                    {
                        "case_id": case.soar_platform_info.case_id,
                        "platform_type": case.soar_platform_info.platform_type,  # pylint: disable=line-too-long
                    }
                    if case.soar_platform_info
                    else None
                ),
                "alert_ids": case.alert_ids,
            }
            for case in result.cases
        ]
    }
    output_formatter(cases_dict, output_format)
