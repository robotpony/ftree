use std::collections::HashSet;
use std::fmt::Write as FmtWrite;
use std::fs;
use std::path::Path;

use crate::model::{FamilyTree, Sex};
use crate::render::{RenderError, Renderer};
use crate::render::ascii::find_root_families;

// Layout constants
const BOX_W: f32 = 164.0;
const BOX_H: f32 = 52.0;
const H_GAP: f32 = 24.0;   // gap between sibling subtrees and between couple boxes
const V_GAP: f32 = 72.0;   // vertical gap between generation rows
const PADDING: f32 = 24.0; // canvas edge padding

/// SVG family tree renderer.
pub struct SvgRenderer;

impl Renderer for SvgRenderer {
    fn render(&self, tree: &FamilyTree, output: &Path) -> Result<(), RenderError> {
        let content = render_svg(tree);
        if let Some(parent) = output.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::write(output, content)?;
        Ok(())
    }
}

/// A positioned person box.
#[derive(Debug)]
struct SvgBox {
    x: f32,
    y: f32,
    name: String,
    dates: String,
    sex: Option<Sex>,
}

/// A connector line between elements.
#[derive(Debug)]
struct SvgLine {
    x1: f32,
    y1: f32,
    x2: f32,
    y2: f32,
}

/// Compute the minimum width needed for the subtree rooted at `xref`.
fn measure(tree: &FamilyTree, xref: &str, visited: &mut HashSet<String>) -> f32 {
    if !visited.insert(xref.to_string()) {
        return BOX_W;
    }

    let indi = match tree.individuals.get(xref) {
        Some(i) => i,
        None => return BOX_W,
    };

    if indi.family_as_spouse.is_empty() {
        return BOX_W;
    }

    let fam_xref = &indi.family_as_spouse[0];
    let fam = match tree.families.get(fam_xref) {
        Some(f) => f,
        None => return BOX_W,
    };

    let has_spouse = spouse_in_family(tree, xref, fam_xref).is_some();
    let couple_width = if has_spouse {
        2.0 * BOX_W + H_GAP
    } else {
        BOX_W
    };

    let unvisited_children: Vec<&String> = fam
        .children
        .iter()
        .filter(|c| !visited.contains(c.as_str()))
        .collect();

    if unvisited_children.is_empty() {
        return couple_width;
    }

    let child_widths: f32 = unvisited_children
        .iter()
        .map(|c| measure(tree, c, visited))
        .sum();
    let children_total = child_widths + H_GAP * (unvisited_children.len() - 1) as f32;

    couple_width.max(children_total)
}

/// Place all boxes and lines for the subtree rooted at `xref` starting at (start_x, y).
/// Returns the total width consumed.
fn place(
    boxes: &mut Vec<SvgBox>,
    lines: &mut Vec<SvgLine>,
    tree: &FamilyTree,
    xref: &str,
    start_x: f32,
    y: f32,
    visited: &mut HashSet<String>,
) -> f32 {
    if visited.contains(xref) {
        return 0.0;
    }

    let total_width = {
        let mut v = visited.clone();
        measure(tree, xref, &mut v)
    };

    visited.insert(xref.to_string());

    let indi = match tree.individuals.get(xref) {
        Some(i) => i,
        None => return total_width,
    };

    let has_families = !indi.family_as_spouse.is_empty();

    if !has_families {
        boxes.push(make_box(tree, xref, start_x + (total_width - BOX_W) / 2.0, y));
        return total_width;
    }

    let fam_xref = &indi.family_as_spouse[0].clone();
    let fam = match tree.families.get(fam_xref) {
        Some(f) => f,
        None => {
            boxes.push(make_box(tree, xref, start_x + (total_width - BOX_W) / 2.0, y));
            return total_width;
        }
    };

    let spouse_xref = spouse_in_family(tree, xref, fam_xref).map(|s| s.to_string());
    let has_spouse = spouse_xref.is_some();
    let couple_width = if has_spouse {
        2.0 * BOX_W + H_GAP
    } else {
        BOX_W
    };

    let unvisited_children: Vec<String> = fam
        .children
        .iter()
        .filter(|c| !visited.contains(c.as_str()))
        .cloned()
        .collect();

    let children_total = if unvisited_children.is_empty() {
        0.0
    } else {
        let mut v = visited.clone();
        let w: f32 = unvisited_children
            .iter()
            .map(|c| measure(tree, c, &mut v))
            .sum();
        w + H_GAP * (unvisited_children.len() - 1) as f32
    };

    // Center couple and children relative to total_width
    let couple_offset = (total_width - couple_width) / 2.0;
    let couple_x = start_x + couple_offset;

    // Place person box
    boxes.push(make_box(tree, xref, couple_x, y));

    // Place spouse box + couple connector
    let couple_center_x = if let Some(ref sx) = spouse_xref {
        let spouse_x = couple_x + BOX_W + H_GAP;
        if !visited.contains(sx) {
            boxes.push(make_box(tree, sx, spouse_x, y));
        }
        // Couple connector (horizontal line between the two boxes)
        lines.push(SvgLine {
            x1: couple_x + BOX_W,
            y1: y + BOX_H / 2.0,
            x2: spouse_x,
            y2: y + BOX_H / 2.0,
        });
        couple_x + BOX_W + H_GAP / 2.0
    } else {
        couple_x + BOX_W / 2.0
    };

    if !unvisited_children.is_empty() {
        let child_y = y + BOX_H + V_GAP;
        let bar_y = y + BOX_H + V_GAP / 2.0;

        let children_offset = (total_width - children_total) / 2.0;
        let mut cx = start_x + children_offset;

        // Collect child center x positions for bar drawing
        let mut child_centers: Vec<f32> = Vec::new();
        let mut child_widths: Vec<f32> = Vec::new();

        for child_xref in &unvisited_children {
            let mut v = visited.clone();
            let w = measure(tree, child_xref, &mut v);
            child_widths.push(w);
        }

        for (i, _) in unvisited_children.iter().enumerate() {
            let w = child_widths[i];
            child_centers.push(cx + w / 2.0);
            cx += w + H_GAP;
        }

        // Vertical drop from couple to horizontal bar
        lines.push(SvgLine {
            x1: couple_center_x,
            y1: y + BOX_H,
            x2: couple_center_x,
            y2: bar_y,
        });

        // Horizontal bar (if multiple children)
        if child_centers.len() > 1 {
            lines.push(SvgLine {
                x1: *child_centers.first().unwrap(),
                y1: bar_y,
                x2: *child_centers.last().unwrap(),
                y2: bar_y,
            });
        } else if child_centers.len() == 1 {
            // Single child: just extend the vertical line
            lines.last_mut().unwrap().y2 = child_y;
        }

        // Drop from bar to each child, then recurse
        let mut cx = start_x + children_offset;
        for (i, child_xref) in unvisited_children.iter().enumerate() {
            let w = child_widths[i];
            let child_center = child_centers[i];

            if child_centers.len() > 1 {
                // Drop from bar to child top
                lines.push(SvgLine {
                    x1: child_center,
                    y1: bar_y,
                    x2: child_center,
                    y2: child_y,
                });
            }

            place(boxes, lines, tree, child_xref, cx, child_y, visited);
            cx += w + H_GAP;
        }
    }

    total_width
}

fn make_box(tree: &FamilyTree, xref: &str, x: f32, y: f32) -> SvgBox {
    let indi = tree.individuals.get(xref);
    let name = indi
        .map(|i| i.display_name().to_string())
        .unwrap_or_else(|| xref.to_string());

    let birth_year = indi
        .and_then(|i| i.birth.as_ref())
        .and_then(|e| e.date.as_ref())
        .and_then(|d| d.year)
        .map(|y| y.to_string());

    let death_year = indi
        .and_then(|i| i.death.as_ref())
        .and_then(|e| e.date.as_ref())
        .and_then(|d| d.year)
        .map(|y| y.to_string());

    let dates = match (birth_year, death_year) {
        (Some(b), Some(d)) => format!("b.{} – d.{}", b, d),
        (Some(b), None) => format!("b.{}", b),
        (None, Some(d)) => format!("d.{}", d),
        (None, None) => String::new(),
    };

    SvgBox {
        x,
        y,
        name,
        dates,
        sex: indi.and_then(|i| i.sex.clone()),
    }
}

fn spouse_in_family<'a>(tree: &'a FamilyTree, indi_xref: &str, fam_xref: &str) -> Option<&'a str> {
    tree.families.get(fam_xref).and_then(|fam| {
        if fam.husband.as_deref() == Some(indi_xref) {
            fam.wife.as_deref()
        } else {
            fam.husband.as_deref()
        }
    })
}

/// Generate the full SVG document for the family tree.
pub fn render_svg(tree: &FamilyTree) -> String {
    let roots = find_root_families(tree);

    if roots.is_empty() {
        return r#"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 40" style="max-width: 100%; height: auto; display: block;">
  <text x="10" y="24" font-family="sans-serif" font-size="14">(no individuals found)</text>
</svg>
"#
        .to_string();
    }

    let mut all_boxes: Vec<SvgBox> = Vec::new();
    let mut all_lines: Vec<SvgLine> = Vec::new();

    let mut offset_y = PADDING;
    let mut visited: HashSet<String> = HashSet::new();

    for (i, root) in roots.iter().enumerate() {
        if i > 0 {
            offset_y += V_GAP;
        }
        let box_start = all_boxes.len();
        place(&mut all_boxes, &mut all_lines, tree, root, PADDING, offset_y, &mut visited);
        offset_y = all_boxes[box_start..]
            .iter()
            .map(|b| b.y + BOX_H)
            .fold(offset_y, f32::max);
    }

    // Compute viewBox
    let max_x = all_boxes
        .iter()
        .map(|b| b.x + BOX_W)
        .fold(0.0_f32, f32::max)
        + PADDING;
    let max_y = all_boxes
        .iter()
        .map(|b| b.y + BOX_H)
        .fold(0.0_f32, f32::max)
        + PADDING;

    let width = max_x.max(200.0);
    let height = max_y.max(100.0);

    let mut out = String::new();
    let _ = writeln!(
        out,
        r#"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" style="max-width: 100%; height: auto; display: block;">"#,
        width = width,
        height = height
    );

    // Styles
    out.push_str(
        r#"  <style>
    .box-male    { fill: #dbeafe; stroke: #3b82f6; stroke-width: 1.5; rx: 4; }
    .box-female  { fill: #fce7f3; stroke: #ec4899; stroke-width: 1.5; rx: 4; }
    .box-unknown { fill: #f3f4f6; stroke: #9ca3af; stroke-width: 1.5; rx: 4; }
    .name        { font-family: sans-serif; font-size: 12px; font-weight: 600; fill: #111827; }
    .dates       { font-family: sans-serif; font-size: 10px; fill: #6b7280; }
    .connector   { stroke: #9ca3af; stroke-width: 1.5; fill: none; }
  </style>
"#,
    );

    // Lines first (behind boxes)
    for line in &all_lines {
        let _ = writeln!(
            out,
            r#"  <line class="connector" x1="{:.1}" y1="{:.1}" x2="{:.1}" y2="{:.1}"/>"#,
            line.x1, line.y1, line.x2, line.y2
        );
    }

    // Boxes
    for b in &all_boxes {
        let class = match &b.sex {
            Some(Sex::Male) => "box-male",
            Some(Sex::Female) => "box-female",
            _ => "box-unknown",
        };

        let name_escaped = xml_escape(&b.name);
        let dates_escaped = xml_escape(&b.dates);

        // Box rect
        let _ = writeln!(
            out,
            r#"  <rect class="{class}" x="{:.1}" y="{:.1}" width="{BOX_W}" height="{BOX_H}" rx="4"/>"#,
            b.x, b.y
        );

        // Name text (centered, upper half)
        let text_x = b.x + BOX_W / 2.0;
        let name_y = if b.dates.is_empty() {
            b.y + BOX_H / 2.0 + 4.5
        } else {
            b.y + BOX_H / 2.0 - 4.0
        };
        let _ = writeln!(
            out,
            r#"  <text class="name" x="{:.1}" y="{:.1}" text-anchor="middle">{}</text>"#,
            text_x, name_y, name_escaped
        );

        // Dates text (centered, lower half)
        if !b.dates.is_empty() {
            let dates_y = b.y + BOX_H / 2.0 + 13.0;
            let _ = writeln!(
                out,
                r#"  <text class="dates" x="{:.1}" y="{:.1}" text-anchor="middle">{}</text>"#,
                text_x, dates_y, dates_escaped
            );
        }
    }

    out.push_str("</svg>\n");
    out
}

/// Escape special XML characters.
fn xml_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::*;

    fn make_test_tree() -> FamilyTree {
        let mut tree = FamilyTree::new();

        let mut john = Individual::new("@I1@".to_string());
        john.name = Some(Name::from_gedcom("John /Smith/"));
        john.sex = Some(Sex::Male);
        john.birth = Some(Event {
            date: Some(Date::parse("1900")),
            place: None,
        });
        john.death = Some(Event {
            date: Some(Date::parse("1980")),
            place: None,
        });
        john.family_as_spouse.push("@F1@".to_string());

        let mut jane = Individual::new("@I2@".to_string());
        jane.name = Some(Name::from_gedcom("Jane /Doe/"));
        jane.sex = Some(Sex::Female);
        jane.family_as_spouse.push("@F1@".to_string());

        let mut bob = Individual::new("@I3@".to_string());
        bob.name = Some(Name::from_gedcom("Robert /Smith/"));
        bob.sex = Some(Sex::Male);
        bob.family_as_child.push("@F1@".to_string());

        let mut fam = Family::new("@F1@".to_string());
        fam.husband = Some("@I1@".to_string());
        fam.wife = Some("@I2@".to_string());
        fam.children.push("@I3@".to_string());

        tree.individuals.insert("@I1@".to_string(), john);
        tree.individuals.insert("@I2@".to_string(), jane);
        tree.individuals.insert("@I3@".to_string(), bob);
        tree.families.insert("@F1@".to_string(), fam);

        tree
    }

    #[test]
    fn test_svg_output_is_valid_xml() {
        let tree = make_test_tree();
        let svg = render_svg(&tree);

        assert!(svg.starts_with("<svg "));
        assert!(svg.ends_with("</svg>\n"));
        assert!(svg.contains("xmlns=\"http://www.w3.org/2000/svg\""));
    }

    #[test]
    fn test_svg_contains_names() {
        let tree = make_test_tree();
        let svg = render_svg(&tree);

        assert!(svg.contains("John Smith"), "should contain John Smith");
        assert!(svg.contains("Jane Doe"), "should contain Jane Doe");
        assert!(svg.contains("Robert Smith"), "should contain Robert Smith");
    }

    #[test]
    fn test_svg_contains_dates() {
        let tree = make_test_tree();
        let svg = render_svg(&tree);

        assert!(svg.contains("b.1900"), "should contain birth year");
        assert!(svg.contains("d.1980"), "should contain death year");
    }

    #[test]
    fn test_svg_sex_classes() {
        let tree = make_test_tree();
        let svg = render_svg(&tree);

        assert!(svg.contains("box-male"), "should have male box class");
        assert!(svg.contains("box-female"), "should have female box class");
    }

    #[test]
    fn test_svg_has_connectors() {
        let tree = make_test_tree();
        let svg = render_svg(&tree);

        assert!(svg.contains("<line"), "should have connector lines");
    }

    #[test]
    fn test_svg_empty_tree() {
        let tree = FamilyTree::new();
        let svg = render_svg(&tree);

        assert!(svg.contains("no individuals found"));
    }

    #[test]
    fn test_svg_xml_escape() {
        assert_eq!(xml_escape("a & b"), "a &amp; b");
        assert_eq!(xml_escape("<tag>"), "&lt;tag&gt;");
        assert_eq!(xml_escape("\"quote\""), "&quot;quote&quot;");
    }

    #[test]
    fn test_measure_leaf() {
        let mut tree = FamilyTree::new();
        let mut indi = Individual::new("@I1@".to_string());
        indi.name = Some(Name::from_gedcom("Solo /Person/"));
        tree.individuals.insert("@I1@".to_string(), indi);

        let mut visited = HashSet::new();
        let w = measure(&tree, "@I1@", &mut visited);
        assert_eq!(w, BOX_W);
    }

    #[test]
    fn test_measure_couple_no_children() {
        let tree = make_test_tree();
        // Create a tree with couple but no children
        let mut t2 = FamilyTree::new();
        let mut john = Individual::new("@I1@".to_string());
        john.name = Some(Name::from_gedcom("John /Smith/"));
        john.family_as_spouse.push("@F1@".to_string());
        let jane = {
            let mut j = Individual::new("@I2@".to_string());
            j.name = Some(Name::from_gedcom("Jane /Doe/"));
            j.family_as_spouse.push("@F1@".to_string());
            j
        };
        let mut fam = Family::new("@F1@".to_string());
        fam.husband = Some("@I1@".to_string());
        fam.wife = Some("@I2@".to_string());
        t2.individuals.insert("@I1@".to_string(), john);
        t2.individuals.insert("@I2@".to_string(), jane);
        t2.families.insert("@F1@".to_string(), fam);

        let _ = tree; // silence unused warning
        let mut visited = HashSet::new();
        let w = measure(&t2, "@I1@", &mut visited);
        assert_eq!(w, 2.0 * BOX_W + H_GAP);
    }

    #[test]
    fn test_place_produces_three_boxes() {
        let tree = make_test_tree();
        let mut boxes = Vec::new();
        let mut lines = Vec::new();
        let mut visited = HashSet::new();
        place(&mut boxes, &mut lines, &tree, "@I1@", 0.0, 0.0, &mut visited);

        assert_eq!(boxes.len(), 3, "should place 3 boxes (John, Jane, Robert)");
        assert!(!lines.is_empty(), "should have connector lines");
    }
}
