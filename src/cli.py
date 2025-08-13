"""Command-line interface for ftree."""

import sys
import argparse
from pathlib import Path
from .parser import GedcomParser
from .renderer import AsciiRenderer
from .family_formatter import FamilyFormatter
from .html_renderer import HtmlRenderer


def view_command(args):
    """Handle the view command."""
    filepath = args.filename
    
    # Check if file exists
    if not Path(filepath).exists():
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        return 1
    
    try:
        # Parse the GEDCOM file
        parser = GedcomParser()
        tree = parser.parse_file(filepath)
        
        # Choose output format
        if args.grouped:
            # Use family-grouped format
            formatter = FamilyFormatter(tree)
            output = formatter.format_grouped_families()
        else:
            # Use traditional tree format
            renderer = AsciiRenderer(tree)
            output = renderer.render(
                show_places=args.places,
                show_marriage=args.marriage
            )
        
        print(output)
        return 0
        
    except Exception as e:
        print(f"Error parsing file: {e}", file=sys.stderr)
        return 1


def check_command(args):
    """Handle the check command."""
    filepath = args.filename
    
    # Check if file exists
    if not Path(filepath).exists():
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        return 1
    
    try:
        # Parse the GEDCOM file
        parser = GedcomParser()
        tree = parser.parse_file(filepath)
        
        # Basic statistics
        print(f"File: {filepath}")
        print(f"Individuals: {len(tree.individuals)}")
        print(f"Families: {len(tree.families)}")
        
        # Check for missing data
        missing_birth = 0
        missing_death = 0
        missing_name = 0
        
        for individual in tree.individuals.values():
            if not individual.given_name and not individual.surname:
                missing_name += 1
            if not individual.birth_date:
                missing_birth += 1
            if not individual.death_date:
                missing_death += 1
        
        if missing_name > 0:
            print(f"Warning: {missing_name} individuals missing names")
        if missing_birth > 0:
            print(f"Info: {missing_birth} individuals missing birth dates")
        if missing_death > 0:
            print(f"Info: {missing_death} individuals missing death dates")
        
        print("File check complete")
        return 0
        
    except Exception as e:
        print(f"Error checking file: {e}", file=sys.stderr)
        return 1


def export_command(args):
    """Handle the export command."""
    filepath = args.filename
    
    # Check if file exists
    if not Path(filepath).exists():
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        return 1
    
    try:
        # Parse the GEDCOM file
        parser = GedcomParser()
        tree = parser.parse_file(filepath)
        
        # Generate output based on format
        if args.format == 'html':
            renderer = HtmlRenderer(tree)
            title = f"Family Tree - {Path(filepath).stem}"
            output = renderer.render(
                theme=args.theme,
                include_places=not args.no_places,
                include_photos=not args.no_photos,
                title=title
            )
            
            # Determine output filename
            output_path = Path(filepath).with_suffix('.html')
            if hasattr(args, 'output') and args.output:
                output_path = Path(args.output)
            
            # Write HTML file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            
            print(f"HTML export saved to: {output_path}")
            
        elif args.format == 'svg':
            print("SVG export not yet implemented")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Error exporting file: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog='ftree',
        description='Family tree viewer - Plot and lint GEDCOM files for genealogy'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # View command
    view_parser = subparsers.add_parser('view', help='View a family tree in ASCII format')
    view_parser.add_argument('filename', help='GEDCOM file to view')
    view_parser.add_argument('--places', action='store_true', 
                           help='Include birth/death places')
    view_parser.add_argument('--marriage', action='store_true',
                           help='Include marriage dates')
    view_parser.add_argument('--grouped', action='store_true',
                           help='Group families together with sorted children')
    view_parser.set_defaults(func=view_command)
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check a file for validity')
    check_parser.add_argument('filename', help='GEDCOM file to check')
    check_parser.set_defaults(func=check_command)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export to various formats')
    export_parser.add_argument('filename', help='GEDCOM file to export')
    export_parser.add_argument('--format', choices=['svg', 'html'], 
                              default='html', help='Output format')
    export_parser.add_argument('--output', '-o', help='Output file path')
    export_parser.add_argument('--theme', choices=['default'], default='default',
                              help='CSS theme for HTML output')
    export_parser.add_argument('--no-places', action='store_true',
                              help='Exclude birth/death places from HTML output')
    export_parser.add_argument('--no-photos', action='store_true',
                              help='Exclude photos from HTML output')
    export_parser.set_defaults(func=export_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate command
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())