use std::fmt::Write as FmtWrite;
use std::fs;
use std::path::Path;

use crate::model::FamilyTree;
use crate::render::{RenderError, Renderer};

/// Layout orientation for ASCII tree rendering.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Layout {
    TopDown,
    Horizontal,
}

impl Layout {
    pub fn parse(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "topdown" | "top-down" => Some(Layout::TopDown),
            "horizontal" | "horiz" => Some(Layout::Horizontal),
            _ => None,
        }
    }
}

/// ASCII tree renderer. Writes a single text file (or stdout content).
pub struct AsciiRenderer {
    pub layout: Layout,
}

impl Renderer for AsciiRenderer {
    fn render(&self, tree: &FamilyTree, output: &Path) -> Result<(), RenderError> {
        let content = self.render_to_string(tree);
        if let Some(parent) = output.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::write(output, content)?;
        Ok(())
    }
}

impl AsciiRenderer {
    /// Render the full tree to a string.
    pub fn render_to_string(&self, tree: &FamilyTree) -> String {
        let groups = find_root_families(tree);

        if groups.is_empty() {
            return String::from("(no individuals found)\n");
        }

        let mut out = String::new();
        for (i, root_xref) in groups.iter().enumerate() {
            if i > 0 {
                out.push('\n');
            }
            match self.layout {
                Layout::Horizontal => render_horizontal(&mut out, tree, root_xref, "", true),
                Layout::TopDown => {
                    let lines = render_topdown_tree(tree, root_xref);
                    for line in lines {
                        let _ = writeln!(out, "{}", line);
                    }
                }
            }
        }
        out
    }
}

/// Find root ancestors: individuals with no FAMC (not a child in any family).
/// Returns xrefs sorted for deterministic output.
/// If an individual has family_as_spouse entries, they're preferred as roots.
pub fn find_root_families(tree: &FamilyTree) -> Vec<String> {
    let mut roots: Vec<String> = tree
        .individuals
        .values()
        .filter(|i| i.family_as_child.is_empty())
        .filter(|i| !i.family_as_spouse.is_empty())
        .map(|i| i.xref.clone())
        .collect();

    roots.sort();
    roots.dedup();

    // If no roots with families found, fall back to any individual with no parents
    if roots.is_empty() {
        roots = tree
            .individuals
            .values()
            .filter(|i| i.family_as_child.is_empty())
            .map(|i| i.xref.clone())
            .collect();
        roots.sort();
    }

    // Deduplicate: if both husband and wife of same family are roots,
    // keep only the husband (or first alphabetically) to avoid duplicate trees
    let mut seen_families = std::collections::HashSet::new();
    let mut deduped = Vec::new();
    for xref in &roots {
        if let Some(indi) = tree.individuals.get(xref) {
            let dominated = indi.family_as_spouse.iter().any(|f| seen_families.contains(f));
            if !dominated {
                for f in &indi.family_as_spouse {
                    seen_families.insert(f.clone());
                }
                deduped.push(xref.clone());
            }
        }
    }

    deduped
}

/// Get display label for an individual: "Name" or xref fallback.
fn label(tree: &FamilyTree, xref: &str) -> String {
    tree.individuals
        .get(xref)
        .map(|i| i.display_name().to_string())
        .unwrap_or_else(|| xref.to_string())
}

/// Get the spouse xref for a given individual in a given family.
fn spouse_in_family<'a>(tree: &'a FamilyTree, indi_xref: &str, fam_xref: &str) -> Option<&'a str> {
    tree.families.get(fam_xref).and_then(|fam| {
        if fam.husband.as_deref() == Some(indi_xref) {
            fam.wife.as_deref()
        } else {
            fam.husband.as_deref()
        }
    })
}

// ─── Horizontal layout ──────────────────────────────────────────────

/// Entry point for horizontal rendering of one root.
fn render_horizontal(out: &mut String, tree: &FamilyTree, xref: &str, prefix: &str, is_last: bool) {
    render_horiz_node(out, tree, xref, prefix, is_last, true);
}

/// Recursive horizontal tree renderer.
/// `is_root_call` distinguishes the top-level call (no connector prefix) from children.
fn render_horiz_node(
    out: &mut String,
    tree: &FamilyTree,
    xref: &str,
    prefix: &str,
    is_last: bool,
    is_root_call: bool,
) {
    let indi = match tree.individuals.get(xref) {
        Some(i) => i,
        None => return,
    };

    let person_label = label(tree, xref);

    if indi.family_as_spouse.is_empty() {
        // Leaf: no families
        let connector = if is_root_call {
            ""
        } else if is_last {
            "└── "
        } else {
            "├── "
        };
        let _ = writeln!(out, "{}{}{}", prefix, connector, person_label);
        return;
    }

    for (fi, fam_xref) in indi.family_as_spouse.iter().enumerate() {
        let fam = match tree.families.get(fam_xref) {
            Some(f) => f,
            None => continue,
        };

        let spouse_label = spouse_in_family(tree, xref, fam_xref)
            .map(|sx| format!(" ── {}", label(tree, sx)))
            .unwrap_or_default();

        if fi == 0 {
            let connector = if is_root_call {
                ""
            } else if is_last {
                "└── "
            } else {
                "├── "
            };
            let _ = writeln!(out, "{}{}{}{}", prefix, connector, person_label, spouse_label);
        } else {
            // Additional marriages on separate line
            let spacer = if is_root_call {
                ""
            } else if is_last {
                "    "
            } else {
                "│   "
            };
            let padding = " ".repeat(person_label.len());
            let _ = writeln!(out, "{}{}{}{}", prefix, spacer, padding, spouse_label);
        }

        // Build prefix for children
        let child_prefix = if is_root_call {
            String::new()
        } else if is_last {
            format!("{}    ", prefix)
        } else {
            format!("{}│   ", prefix)
        };

        for (ci, child_xref) in fam.children.iter().enumerate() {
            let child_is_last = ci == fam.children.len() - 1
                && fi == indi.family_as_spouse.len() - 1;
            render_horiz_node(out, tree, child_xref, &child_prefix, child_is_last, false);
        }
    }
}

// ─── Top-down box layout ────────────────────────────────────────────

/// A positioned box in the top-down layout.
struct BoxNode {
    text: String,
    width: usize,
}

impl BoxNode {
    fn new(text: &str) -> Self {
        let width = text.len() + 4; // "│ " + text + " │"
        BoxNode {
            text: text.to_string(),
            width,
        }
    }

    fn render_top(&self) -> String {
        format!("┌{}┐", "─".repeat(self.width - 2))
    }

    fn render_mid(&self) -> String {
        format!("│ {} │", self.text)
    }

    fn render_bot(&self) -> String {
        format!("└{}┘", "─".repeat(self.width - 2))
    }
}

/// Render a top-down tree for a root ancestor, returning lines.
fn render_topdown_tree(tree: &FamilyTree, root_xref: &str) -> Vec<String> {
    let mut lines = Vec::new();
    render_topdown_family(&mut lines, tree, root_xref, 0);
    lines
}

fn render_topdown_family(lines: &mut Vec<String>, tree: &FamilyTree, xref: &str, depth: usize) {
    let indi = match tree.individuals.get(xref) {
        Some(i) => i,
        None => return,
    };

    let indent = "  ".repeat(depth);

    for fam_xref in &indi.family_as_spouse {
        let fam = match tree.families.get(fam_xref) {
            Some(f) => f,
            None => continue,
        };

        // Couple boxes
        let person_box = BoxNode::new(&label(tree, xref));
        let spouse_box = spouse_in_family(tree, xref, fam_xref)
            .map(|sx| BoxNode::new(&label(tree, sx)));

        match &spouse_box {
            Some(sb) => {
                let gap = "   ";
                lines.push(format!("{}{}{}{}", indent, person_box.render_top(), gap, sb.render_top()));
                lines.push(format!("{}{}───{}", indent, person_box.render_mid(), sb.render_mid()));
                lines.push(format!("{}{}{}{}", indent, person_box.render_bot(), gap, sb.render_bot()));
            }
            None => {
                lines.push(format!("{}{}", indent, person_box.render_top()));
                lines.push(format!("{}{}", indent, person_box.render_mid()));
                lines.push(format!("{}{}", indent, person_box.render_bot()));
            }
        }

        // Children
        if !fam.children.is_empty() {
            let couple_center = indent.len() + person_box.width / 2;
            let center_pad = " ".repeat(couple_center);
            lines.push(format!("{}│", center_pad));

            for (ci, child_xref) in fam.children.iter().enumerate() {
                let is_last = ci == fam.children.len() - 1;
                let connector = if is_last { "└── " } else { "├── " };
                let child_label = label(tree, child_xref);
                lines.push(format!("{}{}{}", center_pad, connector, child_label));

                // Recurse for children who have their own families
                if let Some(child) = tree.individuals.get(child_xref.as_str()) {
                    if !child.family_as_spouse.is_empty() {
                        render_topdown_family(lines, tree, child_xref, depth + 1);
                    }
                }
            }
        }
    }

    // Individual with no families
    if indi.family_as_spouse.is_empty() {
        let person_box = BoxNode::new(&label(tree, xref));
        lines.push(format!("{}{}", indent, person_box.render_top()));
        lines.push(format!("{}{}", indent, person_box.render_mid()));
        lines.push(format!("{}{}", indent, person_box.render_bot()));
    }
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
        john.family_as_spouse.push("@F1@".to_string());

        let mut jane = Individual::new("@I2@".to_string());
        jane.name = Some(Name::from_gedcom("Jane /Doe/"));
        jane.sex = Some(Sex::Female);
        jane.family_as_spouse.push("@F1@".to_string());

        let mut bob = Individual::new("@I3@".to_string());
        bob.name = Some(Name::from_gedcom("Robert /Smith/"));
        bob.sex = Some(Sex::Male);
        bob.family_as_child.push("@F1@".to_string());

        let mut alice = Individual::new("@I4@".to_string());
        alice.name = Some(Name::from_gedcom("Alice /Smith/"));
        alice.sex = Some(Sex::Female);
        alice.family_as_child.push("@F1@".to_string());

        let mut fam = Family::new("@F1@".to_string());
        fam.husband = Some("@I1@".to_string());
        fam.wife = Some("@I2@".to_string());
        fam.children.push("@I3@".to_string());
        fam.children.push("@I4@".to_string());

        tree.individuals.insert("@I1@".to_string(), john);
        tree.individuals.insert("@I2@".to_string(), jane);
        tree.individuals.insert("@I3@".to_string(), bob);
        tree.individuals.insert("@I4@".to_string(), alice);
        tree.families.insert("@F1@".to_string(), fam);

        tree
    }

    fn make_multigenerational_tree() -> FamilyTree {
        let mut tree = make_test_tree();

        // Robert marries Mary, has a child Tom
        let mut mary = Individual::new("@I5@".to_string());
        mary.name = Some(Name::from_gedcom("Mary /Jones/"));
        mary.sex = Some(Sex::Female);
        mary.family_as_spouse.push("@F2@".to_string());

        tree.individuals.get_mut("@I3@").unwrap().family_as_spouse.push("@F2@".to_string());

        let mut tom = Individual::new("@I6@".to_string());
        tom.name = Some(Name::from_gedcom("Tom /Smith/"));
        tom.sex = Some(Sex::Male);
        tom.family_as_child.push("@F2@".to_string());

        let mut fam2 = Family::new("@F2@".to_string());
        fam2.husband = Some("@I3@".to_string());
        fam2.wife = Some("@I5@".to_string());
        fam2.children.push("@I6@".to_string());

        tree.individuals.insert("@I5@".to_string(), mary);
        tree.individuals.insert("@I6@".to_string(), tom);
        tree.families.insert("@F2@".to_string(), fam2);

        tree
    }

    #[test]
    fn test_find_root_families() {
        let tree = make_test_tree();
        let roots = find_root_families(&tree);
        // John is root (no FAMC, has FAMS). Jane also has no FAMC but
        // is in the same family, so should be deduped.
        assert_eq!(roots.len(), 1);
    }

    #[test]
    fn test_find_root_families_multigenerational() {
        let tree = make_multigenerational_tree();
        let roots = find_root_families(&tree);
        // Only the grandparent generation should be roots
        // Mary has no FAMC but her family @F2@ is reached via Robert
        // John and Jane share @F1@, so one root. Mary shares @F2@ with Robert (who has FAMC).
        assert!(!roots.is_empty());
        // Root should not include Robert (he has FAMC)
        assert!(!roots.contains(&"@I3@".to_string()));
    }

    #[test]
    fn test_horizontal_basic() {
        let tree = make_test_tree();
        let renderer = AsciiRenderer { layout: Layout::Horizontal };
        let output = renderer.render_to_string(&tree);

        assert!(output.contains("John Smith"));
        assert!(output.contains("Jane Doe"));
        assert!(output.contains("Robert Smith"));
        assert!(output.contains("Alice Smith"));
        // Should have tree connectors
        assert!(output.contains("──"));
    }

    #[test]
    fn test_horizontal_multigenerational() {
        let tree = make_multigenerational_tree();
        let renderer = AsciiRenderer { layout: Layout::Horizontal };
        let output = renderer.render_to_string(&tree);

        assert!(output.contains("John Smith"));
        assert!(output.contains("Tom Smith"));
        assert!(output.contains("Mary Jones"));
    }

    #[test]
    fn test_topdown_basic() {
        let tree = make_test_tree();
        let renderer = AsciiRenderer { layout: Layout::TopDown };
        let output = renderer.render_to_string(&tree);

        // Should contain boxes
        assert!(output.contains("┌"));
        assert!(output.contains("│ John Smith │"));
        assert!(output.contains("│ Jane Doe │"));
        // Children listed
        assert!(output.contains("Robert Smith"));
        assert!(output.contains("Alice Smith"));
    }

    #[test]
    fn test_topdown_multigenerational() {
        let tree = make_multigenerational_tree();
        let renderer = AsciiRenderer { layout: Layout::TopDown };
        let output = renderer.render_to_string(&tree);

        assert!(output.contains("John Smith"));
        assert!(output.contains("Tom Smith"));
    }

    #[test]
    fn test_empty_tree() {
        let tree = FamilyTree::new();
        let renderer = AsciiRenderer { layout: Layout::Horizontal };
        let output = renderer.render_to_string(&tree);
        assert!(output.contains("no individuals found"));
    }

    #[test]
    fn test_layout_parse() {
        assert_eq!(Layout::parse("topdown"), Some(Layout::TopDown));
        assert_eq!(Layout::parse("top-down"), Some(Layout::TopDown));
        assert_eq!(Layout::parse("horizontal"), Some(Layout::Horizontal));
        assert_eq!(Layout::parse("horiz"), Some(Layout::Horizontal));
        assert_eq!(Layout::parse("invalid"), None);
    }

    #[test]
    fn test_disconnected_groups() {
        let mut tree = FamilyTree::new();

        // Group 1
        let mut a = Individual::new("@I1@".to_string());
        a.name = Some(Name::from_gedcom("Person /A/"));
        a.family_as_spouse.push("@F1@".to_string());

        let mut b = Individual::new("@I2@".to_string());
        b.name = Some(Name::from_gedcom("Person /B/"));
        b.family_as_child.push("@F1@".to_string());

        let mut f1 = Family::new("@F1@".to_string());
        f1.husband = Some("@I1@".to_string());
        f1.children.push("@I2@".to_string());

        // Group 2
        let mut c = Individual::new("@I3@".to_string());
        c.name = Some(Name::from_gedcom("Person /C/"));
        c.family_as_spouse.push("@F2@".to_string());

        let mut d = Individual::new("@I4@".to_string());
        d.name = Some(Name::from_gedcom("Person /D/"));
        d.family_as_child.push("@F2@".to_string());

        let mut f2 = Family::new("@F2@".to_string());
        f2.husband = Some("@I3@".to_string());
        f2.children.push("@I4@".to_string());

        tree.individuals.insert("@I1@".to_string(), a);
        tree.individuals.insert("@I2@".to_string(), b);
        tree.individuals.insert("@I3@".to_string(), c);
        tree.individuals.insert("@I4@".to_string(), d);
        tree.families.insert("@F1@".to_string(), f1);
        tree.families.insert("@F2@".to_string(), f2);

        let roots = find_root_families(&tree);
        assert_eq!(roots.len(), 2);

        let renderer = AsciiRenderer { layout: Layout::Horizontal };
        let output = renderer.render_to_string(&tree);
        assert!(output.contains("Person A"));
        assert!(output.contains("Person C"));
    }
}
