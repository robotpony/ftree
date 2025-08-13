#!/usr/bin/env python3
"""
Test script to generate HTML output from sample GEDCOM files.
This script validates the HTML rendering improvements.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import GedcomParser
from src.html_renderer import HtmlRenderer

def test_html_output():
    """Test HTML output generation with sample GEDCOM files."""
    
    # Test files to process
    test_files = [
        "samples/Harry Potter.ged",
        "samples/Simpsons Cartoon.ged", 
        "samples/test_details.ged"
    ]
    
    for gedcom_file in test_files:
        if not os.path.exists(gedcom_file):
            print(f"Skipping {gedcom_file} - file not found")
            continue
            
        print(f"\nProcessing {gedcom_file}...")
        
        try:
            # Parse GEDCOM file
            parser = GedcomParser()
            tree = parser.parse_file(gedcom_file)
            
            # Create HTML renderer
            renderer = HtmlRenderer(tree)
            
            # Generate HTML with enhanced features
            html_content = renderer.render(
                title=f"Family Tree - {os.path.basename(gedcom_file)}",
                include_places=True,
                include_photos=True
            )
            
            # Save to tmp directory
            base_name = os.path.splitext(os.path.basename(gedcom_file))[0]
            output_file = f"tmp/{base_name}_output.html"
            
            # Ensure tmp directory exists
            os.makedirs("tmp", exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"  ✓ Generated HTML: {output_file}")
            print(f"  ✓ Individuals: {len(tree.individuals)}")
            print(f"  ✓ Families: {len(tree.families)}")
            
            # Validate HTML structure
            validation_results = validate_html_features(html_content)
            for feature, status in validation_results.items():
                status_icon = "✓" if status else "✗"
                print(f"  {status_icon} {feature}")
                
        except Exception as e:
            print(f"  ✗ Error processing {gedcom_file}: {e}")

def validate_html_features(html_content):
    """Validate that HTML contains expected features."""
    features = {
        "Proper indentation": "\n                <div" in html_content,
        "Tree connectors CSS": "tree connectors" in html_content.lower(),
        "Enhanced search": 'placeholder="Search names, dates, occupation, education..."' in html_content,
        "Alpine.js integration": 'x-data="familyTreeApp()"' in html_content,
        "Person metadata": "person-metadata" in html_content,
        "Notes display": "person-notes" in html_content,
        "Generation badges": "generation-badge" in html_content,
        "Marriage connectors": "couple::before" in html_content,
        "Interactive controls": "@click=" in html_content,
        "CSS variables": ":root {" in html_content
    }
    
    return features

if __name__ == "__main__":
    print("HTML Output Test Script")
    print("======================")
    
    test_html_output()
    
    print("\n✓ HTML output test completed.")
    print("Generated files are in tmp/ directory.")
    print("Open any HTML file in a browser to test interactivity.")