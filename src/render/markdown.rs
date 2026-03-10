use std::collections::HashMap;
use std::fmt::Write as FmtWrite;
use std::fs;
use std::path::Path;

use crate::model::{Event, FamilyTree, Individual, Sex};
use crate::render::{RenderError, Renderer};

/// Renders each individual as a separate Markdown file with YAML front-matter
/// and Obsidian-style wikilinks.
pub struct MarkdownRenderer;

impl Renderer for MarkdownRenderer {
    fn render(&self, tree: &FamilyTree, output: &Path) -> Result<(), RenderError> {
        fs::create_dir_all(output)?;

        let name_map = build_filename_map(tree);

        for (xref, indi) in &tree.individuals {
            let filename = &name_map[xref.as_str()];
            let content = render_individual(indi, tree, &name_map);
            let file_path = output.join(format!("{}.md", filename));
            fs::write(file_path, content)?;
        }

        Ok(())
    }
}

/// Build a map from xref → unique filename (without extension).
/// Handles duplicate names by appending a numeric suffix.
fn build_filename_map(tree: &FamilyTree) -> HashMap<String, String> {
    let mut map = HashMap::new();
    let mut name_counts: HashMap<String, usize> = HashMap::new();

    // Sort by xref for deterministic output
    let mut xrefs: Vec<&String> = tree.individuals.keys().collect();
    xrefs.sort();

    for xref in xrefs {
        let indi = &tree.individuals[xref];
        let base_name = indi.display_name().to_string();
        let safe_name = sanitize_filename(&base_name);

        let count = name_counts.entry(safe_name.clone()).or_insert(0);
        *count += 1;

        let filename = if *count == 1 {
            safe_name
        } else {
            format!("{} ({})", safe_name, count)
        };

        map.insert(xref.clone(), filename);
    }

    map
}

/// Remove characters that are problematic in filenames.
fn sanitize_filename(name: &str) -> String {
    name.chars()
        .map(|c| match c {
            '/' | '\\' | ':' | '*' | '?' | '"' | '<' | '>' | '|' | '#' | '^' | '[' | ']' => '-',
            _ => c,
        })
        .collect::<String>()
        .trim()
        .to_string()
}

/// Look up the wikilink for a given xref.
fn wikilink(xref: &str, name_map: &HashMap<String, String>) -> String {
    match name_map.get(xref) {
        Some(filename) => format!("[[{}]]", filename),
        None => xref.to_string(),
    }
}

/// Render a single individual to Markdown with YAML front-matter.
fn render_individual(
    indi: &Individual,
    tree: &FamilyTree,
    name_map: &HashMap<String, String>,
) -> String {
    let mut out = String::new();

    // --- YAML front-matter ---
    out.push_str("---\n");

    // Name
    let display_name = indi.display_name();
    write_yaml_field(&mut out, "name", display_name);

    // Sex
    if let Some(ref sex) = indi.sex {
        let sex_str = match sex {
            Sex::Male => "male",
            Sex::Female => "female",
            Sex::Unknown => "unknown",
        };
        write_yaml_field(&mut out, "sex", sex_str);
    }

    // Birth
    if let Some(ref birth) = indi.birth {
        write_event_yaml(&mut out, "birth", birth);
    }

    // Death
    if let Some(ref death) = indi.death {
        write_event_yaml(&mut out, "death", death);
    }

    // Tags for Obsidian
    let mut tags = Vec::new();
    tags.push("person".to_string());
    if let Some(ref sex) = indi.sex {
        match sex {
            Sex::Male => tags.push("male".to_string()),
            Sex::Female => tags.push("female".to_string()),
            Sex::Unknown => {}
        }
    }

    out.push_str("tags:\n");
    for tag in &tags {
        let _ = writeln!(out, "  - {}", tag);
    }

    out.push_str("---\n\n");

    // --- Body ---

    // Name as heading
    let _ = writeln!(out, "# {}\n", display_name);

    // Vital information
    if indi.birth.is_some() || indi.death.is_some() {
        if let Some(ref birth) = indi.birth {
            let _ = write!(out, "**Born:** {}\n", format_event(birth));
        }
        if let Some(ref death) = indi.death {
            let _ = write!(out, "**Died:** {}\n", format_event(death));
        }
        out.push('\n');
    }

    // Family relationships
    let has_parents = !indi.family_as_child.is_empty();
    let has_spouse_families = !indi.family_as_spouse.is_empty();

    if has_parents {
        out.push_str("## Parents\n\n");
        for fam_xref in &indi.family_as_child {
            if let Some(fam) = tree.families.get(fam_xref) {
                if let Some(ref husb) = fam.husband {
                    let _ = writeln!(out, "- **Father:** {}", wikilink(husb, name_map));
                }
                if let Some(ref wife) = fam.wife {
                    let _ = writeln!(out, "- **Mother:** {}", wikilink(wife, name_map));
                }
            }
        }
        out.push('\n');
    }

    if has_spouse_families {
        for fam_xref in &indi.family_as_spouse {
            if let Some(fam) = tree.families.get(fam_xref) {
                // Spouse
                let spouse_xref = if fam.husband.as_deref() == Some(&indi.xref) {
                    fam.wife.as_deref()
                } else {
                    fam.husband.as_deref()
                };

                if let Some(spouse) = spouse_xref {
                    out.push_str("## Spouse\n\n");
                    let _ = writeln!(out, "- {}", wikilink(spouse, name_map));
                    if let Some(ref marriage) = fam.marriage {
                        let _ = writeln!(out, "- **Married:** {}", format_event(marriage));
                    }
                    out.push('\n');
                }

                // Children
                if !fam.children.is_empty() {
                    out.push_str("## Children\n\n");
                    for child_xref in &fam.children {
                        let _ = writeln!(out, "- {}", wikilink(child_xref, name_map));
                    }
                    out.push('\n');
                }
            }
        }
    }

    // Media references
    let media_with_files: Vec<_> = indi
        .media
        .iter()
        .filter_map(|m| m.file.as_ref())
        .collect();
    if !media_with_files.is_empty() {
        out.push_str("## Media\n\n");
        for file in media_with_files {
            if file.starts_with("http://") || file.starts_with("https://") {
                let _ = writeln!(out, "- [{}]({})", file, file);
            } else {
                let _ = writeln!(out, "- {}", file);
            }
        }
        out.push('\n');
    }

    out
}

fn write_yaml_field(out: &mut String, key: &str, value: &str) {
    // Quote values that could be misinterpreted by YAML parsers
    if value.contains(':')
        || value.contains('#')
        || value.contains('"')
        || value.contains('\'')
        || value.starts_with('@')
        || value.starts_with('{')
        || value.starts_with('[')
    {
        let escaped = value.replace('"', r#"\""#);
        let _ = writeln!(out, "{}: \"{}\"", key, escaped);
    } else {
        let _ = writeln!(out, "{}: {}", key, value);
    }
}

fn write_event_yaml(out: &mut String, prefix: &str, event: &Event) {
    if let Some(ref date) = event.date {
        write_yaml_field(out, &format!("{}_date", prefix), &date.raw);
    }
    if let Some(ref place) = event.place {
        write_yaml_field(out, &format!("{}_place", prefix), &place.raw);
    }
}

fn format_event(event: &Event) -> String {
    match (&event.date, &event.place) {
        (Some(date), Some(place)) => format!("{}, {}", date, place),
        (Some(date), None) => date.to_string(),
        (None, Some(place)) => place.to_string(),
        (None, None) => String::new(),
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
        john.birth = Some(Event {
            date: Some(Date::parse("1 Jan 1900")),
            place: Some(Place::new("Boston, MA, USA")),
        });
        john.death = Some(Event {
            date: Some(Date::parse("31 Dec 1980")),
            place: Some(Place::new("New York, NY, USA")),
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
        fam.marriage = Some(Event {
            date: Some(Date::parse("25 Dec 1925")),
            place: Some(Place::new("Miami, FL, USA")),
        });

        tree.individuals.insert("@I1@".to_string(), john);
        tree.individuals.insert("@I2@".to_string(), jane);
        tree.individuals.insert("@I3@".to_string(), bob);
        tree.families.insert("@F1@".to_string(), fam);

        tree
    }

    #[test]
    fn test_sanitize_filename() {
        assert_eq!(sanitize_filename("John Smith"), "John Smith");
        assert_eq!(sanitize_filename("Windows /2.0/"), "Windows -2.0-");
        assert_eq!(
            sanitize_filename("MS-DOS 8.0 /(Windows Me)/"),
            "MS-DOS 8.0 -(Windows Me)-"
        );
        assert_eq!(sanitize_filename("test:file"), "test-file");
    }

    #[test]
    fn test_build_filename_map_unique_names() {
        let tree = make_test_tree();
        let map = build_filename_map(&tree);

        assert_eq!(map["@I1@"], "John Smith");
        assert_eq!(map["@I2@"], "Jane Doe");
        assert_eq!(map["@I3@"], "Robert Smith");
    }

    #[test]
    fn test_build_filename_map_duplicate_names() {
        let mut tree = FamilyTree::new();

        let mut a = Individual::new("@I1@".to_string());
        a.name = Some(Name::from_gedcom("John /Smith/"));
        let mut b = Individual::new("@I2@".to_string());
        b.name = Some(Name::from_gedcom("John /Smith/"));

        tree.individuals.insert("@I1@".to_string(), a);
        tree.individuals.insert("@I2@".to_string(), b);

        let map = build_filename_map(&tree);

        // One should be "John Smith", the other "John Smith (2)"
        let values: Vec<&String> = map.values().collect();
        assert!(values.contains(&&"John Smith".to_string()));
        assert!(values.contains(&&"John Smith (2)".to_string()));
    }

    #[test]
    fn test_render_individual_front_matter() {
        let tree = make_test_tree();
        let name_map = build_filename_map(&tree);
        let john = &tree.individuals["@I1@"];
        let content = render_individual(john, &tree, &name_map);

        // Check YAML front-matter
        assert!(content.starts_with("---\n"));
        assert!(content.contains("name: John Smith\n"));
        assert!(content.contains("sex: male\n"));
        assert!(content.contains("birth_date: 1 Jan 1900\n"));
        assert!(content.contains("birth_place: Boston, MA, USA\n"));
        assert!(content.contains("death_date: 31 Dec 1980\n"));
        assert!(content.contains("  - person\n"));
        assert!(content.contains("  - male\n"));
    }

    #[test]
    fn test_render_individual_wikilinks() {
        let tree = make_test_tree();
        let name_map = build_filename_map(&tree);
        let john = &tree.individuals["@I1@"];
        let content = render_individual(john, &tree, &name_map);

        // Spouse link
        assert!(content.contains("[[Jane Doe]]"));
        // Child link
        assert!(content.contains("[[Robert Smith]]"));
        // Marriage info
        assert!(content.contains("**Married:**"));
    }

    #[test]
    fn test_render_child_has_parent_links() {
        let tree = make_test_tree();
        let name_map = build_filename_map(&tree);
        let bob = &tree.individuals["@I3@"];
        let content = render_individual(bob, &tree, &name_map);

        assert!(content.contains("## Parents"));
        assert!(content.contains("**Father:** [[John Smith]]"));
        assert!(content.contains("**Mother:** [[Jane Doe]]"));
    }

    #[test]
    fn test_render_individual_body_heading() {
        let tree = make_test_tree();
        let name_map = build_filename_map(&tree);
        let john = &tree.individuals["@I1@"];
        let content = render_individual(john, &tree, &name_map);

        assert!(content.contains("# John Smith\n"));
        assert!(content.contains("**Born:** 1 Jan 1900, Boston, MA, USA\n"));
        assert!(content.contains("**Died:** 31 Dec 1980, New York, NY, USA\n"));
    }

    #[test]
    fn test_yaml_quoting() {
        // Commas are fine unquoted in YAML block scalars
        let mut out = String::new();
        write_yaml_field(&mut out, "place", "Boston, MA, USA");
        assert_eq!(out.trim(), "place: Boston, MA, USA");

        // Colons trigger quoting
        let mut out2 = String::new();
        write_yaml_field(&mut out2, "note", "key: value");
        assert!(out2.contains('"'));

        // Plain values stay unquoted
        let mut out3 = String::new();
        write_yaml_field(&mut out3, "name", "John Smith");
        assert!(!out3.contains('"'));
    }

    #[test]
    fn test_wikilink_lookup() {
        let mut map = HashMap::new();
        map.insert("@I1@".to_string(), "John Smith".to_string());

        assert_eq!(wikilink("@I1@", &map), "[[John Smith]]");
        assert_eq!(wikilink("@I99@", &map), "@I99@");
    }
}
